# **[Pattern] Security Approaches Reference Guide**

---
## **Overview**
The **Security Approaches** pattern defines a structured methodology for implementing security controls across applications, systems, and infrastructure. It categorizes security practices into *defense-in-depth*, *security by design*, and *adaptive security*, ensuring resilience against evolving threats. This guide provides a taxonomy of security strategies, implementation best practices, and trade-offs to help architects and developers select and combine the right approaches for their use cases.

---
## **Schema Reference**
Below is a structured breakdown of security approaches, their key characteristics, and applicable scenarios.

| **Category**               | **Subcategory**               | **Description**                                                                                     | **Use Case**                                                                                     | **Trade-offs**                                                                                     |
|----------------------------|-------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Defense-in-Depth**       | **Layered Controls**          | Combines multiple security layers (e.g., perimeter, network, application, and data layers).         | Enterprise systems, cloud deployments, critical infrastructure                                 | Higher operational complexity; overhead in maintenance                                           |
|                            | **Fail-Secure Design**        | Assumes failure and designs systems to degrade to a safe state.                                     | High-availability systems (e.g., financial transactions, healthcare)                            | May increase cost of recovery or downtime                                                           |
|                            | **Least Privilege**            | Grants minimum permissions required for functionality.                                              | Privileged access management, containerized environments                                        | Requires frequent permission audits; steep learning curve for admins                              |
| **Security by Design**     | **Zero Trust Architecture**   | Never trusts; verifies every access request independently.                                           | Modern cloud-native apps, remote workforces                                                     | Highly detailed identity management; requires continuous monitoring                                 |
|                            | **Secure Defaults**           | Configures systems to be secure by default (e.g., encrypted storage, disabled services).             | Consumer IoT devices, embedded systems                                                           | May limit user flexibility; balancing usability vs. security                                      |
|                            | **Static & Dynamic Analysis** | Integrates pre-deployment code reviews (static) and runtime checks (dynamic).                     | Software development pipelines, DevOps environments                                              | Static analysis may miss runtime vulnerabilities; dynamic analysis adds overhead                |
| **Adaptive Security**      | **Behavioral Analytics**      | Uses ML/AI to detect anomalous patterns (e.g., unusual access times, unexpected data transfers).    | Fraud detection, threat hunting                                                                   | Requires high-quality training data; false positives/negatives possible                          |
|                            | **Context-Aware Access**      | Adjusts permissions based on device, location, or time (e.g., MFA context).                          | BYOD policies, multi-region deployments                                                          | Complex policy management; relies on accurate context signals                                     |
|                            | **Proactive Threat Feeds**    | Integrates real-time threat intelligence (e.g., CVE databases, APT alerts).                          | Enterprise threat monitoring, SOAR systems                                                         | Feed quality varies; may create alert fatigue                                                               |

---
## **Implementation Details**
### **1. Defense-in-Depth**
- **Layered Controls**:
  - **Example**: Use firewalls (perimeter), network segmentation (internal), and application firewalls (runtime).
  - **Tools**: Cloud provider firewalls (AWS Security Groups), WAFs (ModSecurity), IDS/IPS (Snort/Suricata).
  - **Best Practice**: Document each layer’s purpose and failure modes (e.g., "If the WAF fails, the database is still encrypted at rest").

- **Fail-Secure Design**:
  - **Pattern**: Implement circuit breakers (e.g., Hystrix) or fallback mechanisms (e.g., read-only mode on disk corruption).
  - **Example**: A payment system fails gracefully by rejecting transactions instead of crashing.

### **2. Security by Design**
- **Zero Trust**:
  - **Key Components**:
    - Identity Provider (IdP): OAuth 2.0/OpenID Connect (e.g., Azure AD, Okta).
    - Runtime Authentication: Short-lived tokens (JWT), device attestation.
    - Micro-segmentation: Network policies per pod/service (e.g., Calico, AWS VPC).
  - **Implementation**:
    ```mermaid
    graph TD
      A[Client] -->|1. Authenticates| B[IdP]
      B -->|2. JWT Token| C[Application]
      C -->|3. Verifies Token| D[Service A]
      D -->|4. Request Data| E[Database]
    ```

- **Secure Defaults**:
  - **Configuration Templates**: Use tools like Ansible or Terraform to enforce defaults (e.g., disable unneeded services in Docker).
  - **Example**: Enable TLS 1.3 by default in cloud load balancers; disable legacy protocols.

### **3. Adaptive Security**
- **Behavioral Analytics**:
  - **Tools**: SIEM (Splunk), UEBA (Darktrace), or custom ML models (TensorFlow).
  - **Example Rule**:
    ```python
    # Pseudocode for detecting anomalous API calls
    def detect_anomaly(user_activity):
        if (user_activity["outbound_calls"] > 3 and
            user_activity["new_destinations"] > 1):
            trigger_alert("Potential lateral movement")
    ```
  - **Trade-off Mitigation**: Start with low-severity alerts; refine models over time.

- **Context-Aware Access**:
  - **Components**:
    - Device Posture Check: Verify OS patches, antivirus status (e.g., Microsoft Defender for IoT).
    - Geofencing: Restrict access by country/region.
  - **Example Policy**:
    ```json
    {
      "requirements": [
        { "type": "mfa", "value": "tfa" },
        { "type": "device", "key": "antivirus", "value": "enabled" },
        { "type": "geo", "country": ["US", "CA"] }
      ]
    }
    ```

---
## **Query Examples**
### **1. How do I implement Zero Trust for my Kubernetes cluster?**
**Steps**:
1. **Pod-Level Security**:
   - Use PodSecurity Admission (PSA) to enforce restrictions (e.g., no root containers).
   - Example rule in `podsecurity-policy.yaml`:
     ```yaml
     privileged: false
     runAsUser: { rule: "MustRunAsNonRoot" }
     ```
2. **Network Policies**:
   - Apply Calico’s `DenyAll` policy by default, then whitelist traffic:
     ```yaml
     apiVersion: networking.k8s.io/v1
     kind: NetworkPolicy
     metadata:
       name: allow-frontend-to-backend
     spec:
       podSelector: { matchLabels: { app: backend } }
       ingress:
       - from:
         - podSelector: { matchLabels: { app: frontend } }
     ```
3. **Runtime Authentication**:
   - Use SPIFFE/SPIRE to generate short-lived certificates for service-to-service auth.
   - Integrate with Istio for automated mTLS.

**Tools**:
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) for policy enforcement.

---

### **2. How can I detect lateral movement in my environment?**
**Approaches**:
| **Method**               | **Tool**                          | **Implementation**                                                                 |
|--------------------------|-----------------------------------|------------------------------------------------------------------------------------|
| **Endpoint Monitoring**  | CrowdStrike/Falcon                  | Deploy agents to track process execution, file changes, and network connections.   |
| **Network Traffic**      | Zeek/Bro                           | Log and analyze `conn` events for unusual port scans or C2 traffic.                |
| **Log Correlation**      | SIEM (Elasticsearch + Kibana)     | Query for sequences like: `auth_success + priv_esc + lateral_movement`.             |
| **Behavioral AI**        | Darktrace                         | Train on normal traffic patterns; flag deviations (e.g., user accessing unrelated systems). |

**Query (ELK Stack)**:
```json
// Detect user jumping to an unfamiliar host
GET /logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "event": "auth_success" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ],
      "filter": {
        "nested": {
          "path": "user_behavior",
          "query": {
            "bool": {
              "must_not": {
                "term": { "user_behavior.frequent_destinations": "true" }
              }
            }
          }
        }
      }
    }
  }
}
```

---

### **3. How do I enforce least privilege in a containerized environment?**
**Steps**:
1. **Container Runtime**:
   - Use `user: "1000"` in Dockerfiles to run as a non-root user:
     ```dockerfile
     RUN useradd -u 1000 myappuser && \
         chown -R myappuser:myappuser /app
     USER myappuser
     ```
2. **Kubernetes**:
   - Set `runAsNonRoot: true` in PodSecurityContext:
     ```yaml
     securityContext:
       runAsNonRoot: true
       runAsUser: 1000
     ```
3. **Secrets Management**:
   - Avoid embedding secrets in images. Use Kubernetes Secrets or external vaults (HashiCorp Vault).
   - Example Vault integration:
     ```yaml
     spec:
       containers:
       - name: myapp
         env:
         - name: DB_PASSWORD
           valueFrom:
             secretKeyRef:
               name: db-creds
               key: password
     ```

**Tools**:
- [Docker Bench Security](https://github.com/docker/docker-bench-security) (CIS compliance checks).
- [Kyverno](https://kyverno.io/) (Kubernetes policy engine for RBAC validation).

---
## **Related Patterns**
1. **[Secure Coding Practices]**
   - Complements *Security by Design* by integrating secure coding (e.g., input validation, dependency scanning) into development workflows.
   - **Key Overlap**: Static analysis as part of secure defaults.

2. **[Observability for Security]**
   - Enables adaptive security by providing visibility into system behavior for anomaly detection.
   - **Key Overlap**: Behavioral analytics rely on observability data.

3. **[Chaos Engineering]**
   - Tests fail-secure designs by intentionally introducing failures (e.g., killing pods to test recovery).
   - **Key Overlap**: Validates defense-in-depth strategies under stress.

4. **[Secret Management]**
   - Foundational for least privilege and zero trust, ensuring credentials aren’t hardcoded.
   - **Key Overlap**: Required for context-aware access policies.

5. **[Infrastructure as Code (IaC)]**
   - Enforces secure defaults by version-controlling infrastructure templates.
   - **Key Overlap**: Applies to layered controls (e.g., Terraform modules for network segmentation).

---
## **Further Reading**
- **NIST SP 800-53**: Security and Privacy Controls for Federal Systems.
- **OWASP Top 10**: Application security risks (e.g., Broken Access Control maps to least privilege).
- **CIS Controls**: Critical security controls for defense-in-depth (e.g., CIS Control 9: "Monitor and Control Remote Access").
- **Zero Trust Maturity Model (ZTMM)**: Framework for adopting zero trust (Microsoft). [Link](https://docs.microsoft.com/en-us/security/zero-trust/zero-trust-maturity-model).