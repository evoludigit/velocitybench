# **[Pattern] Security Debugging Reference Guide**

## **Overview**
Security Debugging is a systematic approach to diagnosing, reproducing, and resolving security vulnerabilities, misconfigurations, or suspicious behaviors in software, infrastructure, or applications. This pattern helps developers, security practitioners, and DevOps engineers isolate security-related issues by combining structured debugging techniques with security-focused tooling and logging. It covers **pre-mortem analysis** (hypothetical threat modeling), **real-time debugging** (live incident response), and **post-mortem investigations** (root cause analysis). By leveraging structured debugging workflows, you can efficiently hunt for threats, validate security controls, and harden applications without disrupting production.

---

## **Key Concepts & Implementation Details**

### **1. Security Debugging Workflow**
The pattern follows a **5-phase cycle** to ensure thorough investigation:

| **Phase**            | **Objective**                                                                 | **Tools/Techniques**                                                                 |
|----------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Pre-mortem**       | Hypothetical threat modeling to prevent vulnerabilities.                       | STRIDE, DREAD, Attack Trees, Misconfiguration Scanners (e.g., Checkmarx, Prisma)    |
| **Pre-deployment**   | Static analysis to catch security flaws before runtime.                        | SAST (SonarQube, CodeQL), Policy-as-Code (Open Policy Agent), Dependency Scanners    |
| **Runtime Debugging**| Real-time monitoring and debugging of suspicious activity.                   | Runtime Application Self-Protection (RASP), EDR/XDR, Custom Log Analysis (Grafana, ELK) |
| **Post-incident**    | Forensic analysis of exploited vulnerabilities.                                | PCAP Analysis, Memory Forensics (Volatility), SIEM (Splunk, Datadog)                 |
| **Remediation**      | Applying fixes and validating their effectiveness.                           | Automated Scanners (OWASP ZAP), CI/CD Security Gates, Security Test Automation       |

---

### **2. Core Debugging Techniques**
#### **A. Structured Logging for Security**
- **Purpose**: Capture granular security-related events (auth failures, API calls, privilege escalations).
- **Implementation**:
  - Use **structured logging** (JSON, Protobuf) for parasite-free parsing.
  - Log **correlation IDs** to trace requests across services.
  - Example:
    ```json
    {
      "timestamp": "2024-05-20T14:30:00Z",
      "event": "auth_failure",
      "user": "test_user",
      "ip": "192.168.1.100",
      "service": "api-gateway",
      "error": "invalid_credentials",
      "severity": "warning"
    }
    ```

#### **B. Dynamic Analysis (Runtime Debugging)**
- **Tools**:
  - **Debuggers**: `gdb`, `pwndbg`, `Frida` (for binary exploitation debugging).
  - **Runtime Protection**: RASP (e.g., OpenRASP), WAF (ModSecurity).
  - **Network Analysis**: `tcpdump`, Wireshark, `mitmproxy` (for MITM attacks).
- **Example Workflow**:
  1. Reproduce a **buffer overflow** in a vulnerable service.
  2. Attach `gdb` and set breakpoints:
     ```bash
     gdb ./vulnerable_service
     (gdb) break *0x401234
     (gdb) run --args -c "A"$(python -c 'print("A"*200)')
     ```
  3. Analyze stack traces and exploit chains.

#### **C. Static Analysis (Pre-Deployment)**
- **Tools**:
  - **SAST**: SonarQube, CodeQL, Fortify.
  - **Dependency Scanning**: Snyk, Dependabot, Trivy.
  - **Policy Enforcement**: Open Policy Agent (OPA), Kyverno.
- **Example Query (CodeQL)**:
  ```codeql
  class SqlInjection extends Semmle.Code.Queries.Security.SQLInjection {
    // Detects SQL injection patterns in user input.
  }
  ```

#### **D. Memory Forensics (Post-Exploitation)**
- **Tools**: Volatility, Rekall, Ghidra.
- **Example Command (Volatility)**:
  ```bash
  volatility -f memory_dump.hdd pslist  # List running processes
  volatility -f memory_dump.hdd handles  # Find open file handles (potential backdoors)
  ```

#### **E. Misconfiguration Scanning**
- **Tools**: Prisma Cloud, Aqua Security, CIS Benchmark checks.
- **Example CIS Benchmark Rule (AWS)**:
  ```bash
  # Check if IAM policies allow wildcard S3 bucket access
  aws iam get-policy --policy-arn "arn:aws:iam::123456789012:policy/unsafe-policy" | jq '.PolicyDocument.Statement[] | select(.Effect == "Allow" and .Resource == "*")'
  ```

---

## **Schema Reference**
Below is a **standardized schema** for security debugging logs and artifacts.

| **Field**               | **Description**                                                                 | **Data Type**       | **Example Values**                          |
|-------------------------|-------------------------------------------------------------------------------|---------------------|---------------------------------------------|
| `event_id`              | Unique identifier for the security event.                                    | UUID                | `550e8400-e29b-41d4-a716-446655440000`      |
| `timestamp`             | ISO 8601 timestamp of the event.                                             | String (ISO8601)    | `2024-05-20T14:30:00Z`                      |
| `event_type`            | Category of the event (e.g., `auth_failure`, `ddo_mitigation`).              | Enum                | `brute_force_attempt`, `priv_escalation`     |
| `severity`              | Criticality level (from 1-5).                                                | Integer             | `3` (Medium)                                |
| `source_system`         | Originating system (e.g., `api-gateway`, `db`, `kubernetes`).                | String              | `nginx`                                     |
| `user_agent`            | HTTP User-Agent or process name.                                             | String              | `Mozilla/5.0`, `python3`                    |
| `ip_address`            | Source IP (with geo-location if available).                                  | String              | `192.168.1.100` (geo: `US`)                 |
| `request_id`            | Correlation ID for tracing across services.                                   | String              | `req_abc123`                                |
| `payload`               | Raw or sanitized request/response data (base64-encoded if sensitive).       | String (Base64)     | `SGVsbG8=` (decodes to "Hello")             |
| `remediation_status`    | Whether the issue has been fixed.                                           | Boolean             | `true`/false                                 |
| `remediation_notes`     | Steps taken to resolve the issue.                                           | String              | `Patched CVE-2023-1234 in nginx config`     |

---

## **Query Examples**
### **1. Finding Brute-Force Attempts (Grafana/Loki)**
```sql
// Query logs for failed login attempts in the last 24 hours.
{job="auth-service"} | json | filter(severity = "warning" and event = "auth_failure") | count_by(user)
```
**Expected Output**:
```
user         | count
------------|------
test_user   | 15
admin       | 30
```

### **2. Detecting Unauthorized API Calls (ELK Kibana)**
```json
// Alert on API calls from unusual regions.
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event_type": "api_call" } },
        { "range": { "timestamp": { "gte": "now-1d" } } },
        { "term": { "severity": "high" } },
        { "not": { "term": { "geo_region": "US" } } }
      ]
    }
  }
}
```

### **3. Analyzing Buffer Overflow Exploits (GDB)**
```bash
# Attach to a vulnerable process and inspect stack.
gdb -p <PID>
(gdb) x/50xw $esp  # Examine stack memory for shellcode
(gdb) finfo *$esp # Disassemble suspicious code
```

### **4. Finding Hardcoded Secrets (CodeQL)**
```codeql
// Detect hardcoded secrets in source code.
import semantic

class HardcodedSecret extends Semmle.Code.Queries.Security.HardcodedSecret {
  StringExpression secret = this;
  bool isSecret(StringExpression expr) {
    return expr.getType().isSubtypeOf("String") and
           expr.matches("^(?i)(api|password|key|token).*");
  }
}
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------|
| **[Defense in Depth]**           | Layered security controls to slow down attackers.                            | When designing multi-tier security architectures. |
| **[Secure Defaults]**            | Configure systems to minimize attack surface by default.                    | During infrastructure provisioning.            |
| **[Runtime Application Self-Protection (RASP)]** | Active monitoring and blocking of attacks during runtime.            | For web apps with high-risk APIs.              |
| **[Immutable Infrastructure]**   | Prevent tampering by treating infrastructure as read-only.                   | In containerized or serverless deployments.    |
| **[Threat Modeling]**            | Proactively identify and mitigate threats before implementation.           | During architecture design or pre-release.    |

---

## **Best Practices**
1. **Automate Repetitive Checks**:
   - Use **CI/CD pipelines** to run SAST/DAST scans.
   - Example (GitHub Actions):
     ```yaml
     - name: Run SAST Scan
       uses: sonarsource/sonarcloud-github-action@master
       env:
         SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
     ```
2. **Correlate Logs Across Systems**:
   - Use **distributed tracing** (OpenTelemetry, Jaeger) for end-to-end security telemetry.
3. **Simulate Attacks**:
   - Run **red team exercises** (e.g., with Metasploit, Burp Suite).
4. **Document Findings**:
   - Maintain a **threat intelligence database** (e.g., MITRE ATT&CK mappings).
5. **Validate Fixes**:
   - After remediation, re-run **dynamic analysis** to confirm the issue is resolved.

---
## **Troubleshooting Common Issues**
| **Issue**                          | **Cause**                                  | **Solution**                                      |
|------------------------------------|--------------------------------------------|---------------------------------------------------|
| False positives in SAST scans      | Overly broad rules or outdated patterns.    | Refine queries; update tool versions.              |
| Debugging tools don’t attach       | Process is running in a restricted sandbox.| Use `gdbserver` or kernel-level debugging.       |
| Logs are corrupted/incomplete      | Unstructured logs or missing parsing.     | Switch to structured logging (e.g., JSON).        |
| Memory forensics tools fail        | Unsaved memory dump or corrupted file.     | Use `dd` to capture physical memory: `dd if=/dev/mem of=mem_dump.raw`. |

---
## **Further Reading**
- **[OWASP Security Debugging Guide](https://www.owasp.org/)** – Best practices for secure debugging.
- **[MITRE ATT&CK](https://attack.mitre.org/)** – Threat modeling framework.
- **[Google’s Security Debugging Booklet](https://googleprojectzero.blogspot.com/)** – Techniques for binary exploitation.
- **[CIS Benchmarks](https://www.cisecurity.org/)** – Hardened configurations for systems.

---
**Last Updated**: 2024-05-20
**Version**: 1.2