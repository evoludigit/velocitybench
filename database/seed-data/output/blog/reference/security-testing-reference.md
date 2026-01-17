# **[Pattern] Security Testing Reference Guide**

---

## **Overview**
Security Testing is a structured approach to identifying vulnerabilities, threats, and weaknesses in software, systems, or infrastructure by simulating real-world attack scenarios. This pattern serves as a **defensive strategy** to mitigate risks, comply with regulations (e.g., GDPR, PCI-DSS), and protect against cyber threats (e.g., data breaches, ransomware, or insider attacks). It includes a combination of **static and dynamic testing methods**, automated scans, manual assessments, and continuous monitoring to ensure system resilience.

Security Testing is most effective when integrated into the **Software Development Lifecycle (SDLC)** (e.g., DevSecOps) rather than treated as an afterthought. It complements other testing patterns like **Performance Testing**, **Functional Testing**, and **Compliance Testing** by focusing specifically on security controls, authentication mechanisms, encryption, and input validation.

---

## **Schema Reference**

| **Component**               | **Description**                                                                 | **Key Attributes**                                                                                     | **Best Practices**                                                                 |
|-----------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **1. Threat Modeling**      | Identifies potential security threats before implementation.                    | - Attack surface analysis<br>- Asset prioritization<br>- Threat likelihood/risk scoring             | Use **STRIDE** or **PASTA** frameworks; involve security experts early.             |
| **2. Static Application Security Testing (SAST)** | Analyzes source code without execution for vulnerabilities.                   | - False positive rate<br>- Tool integration (e.g., SonarQube, Checkmarx)<br>- Ruleset coverage      | Configure strict rules; suppress only legitimate false positives.                 |
| **3. Dynamic Application Security Testing (DAST)** | Tests running applications for vulnerabilities (e.g., SQLi, XSS).           | - Scope (APIs, web apps, mobile)<br>- Authentication handling<br>- Session management checks       | Use tools like OWASP ZAP or Burp Suite; test in production-like environments.        |
| **4. Penetration Testing**  | Simulates real-world cyberattacks by authorized ethical hackers.               | - Test scope (internal/external)<br>- Regulatory compliance (e.g., ISO 27001)<br>- Report depth     | Schedule quarterly; avoid testing during peak loads.                               |
| **5. Infrastructure Security Testing** | Evaluates cloud, network, or server configurations for misconfigurations.     | - Cloud provider (AWS, Azure, GCP)<br>- IAM policies<br>- Encryption standards (TLS, SSL)          | Use tools like **OpenSCAP** or **Nessus**; automate with CI/CD.                     |
| **6. Dependency Scanning**  | Checks third-party libraries/dependencies for known vulnerabilities.          | - Vulnerability database (NVD, Snyk)<br>- Supply chain risk<br>- Update frequency                      | Integrate with package managers (e.g., npm, Maven); prioritize high-severity CVEs. |
| **7. Compliance Testing**   | Validates adherence to security standards (e.g., OWASP Top 10, HIPAA).        | - Audit logs<br>- Policy alignment<br>- Automated scans vs. manual reviews                          | Use tools like **Qualys** or **PolicyCompliance;** document deviations.             |
| **8. Continuous Security Monitoring** | Real-time detection of anomalies (e.g., unusual access patterns).            | - SIEM integration (e.g., Splunk)<br>- Alert thresholds<br>- Incident response workflows            | Correlate logs with threats; reduce alert fatigue.                                 |
| **9. Social Engineering Testing** | Assesses user susceptibility to phishing/scams via simulated attacks.          | - Email, SMS, or phone-based tests<br>- Employee training impact<br>- Compliance (e.g., FTC)        | Perform annually; include phishing simulations in security awareness programs.      |
| **10. Secure Code Review**   | Manual or automated review of code for security flaws.                        | - Review depth (unit vs. system)<br>- Tool support (e.g., CodeQL)<br>- Developer feedback loops      | Pair with SAST; document fix priorities.                                           |

---

## **Implementation Details**

### **1. Threat Modeling**
- **When to Use**: During **design and pre-development phases**.
- **How to Implement**:
  - Use frameworks like **STRIDE** (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation) or **PASTA** (Application Threat Modeling).
  - Document threats in a **threat matrix** with **mitigation strategies** (e.g., input validation, rate limiting).
  - Example:
    | **Asset**       | **Threat Actor** | **Vulnerability** | **Mitigation**               |
    |-----------------|------------------|-------------------|------------------------------|
    | User Database   | Hacker           | SQL Injection     | Parameterized queries         |
    | API Gateway     | Insider          | Overprivileged Access | Least privilege principle    |

### **2. SAST vs. DAST**
- **SAST**:
  - **Pros**: Early detection, integrates with CI/CD.
  - **Cons**: May miss runtime flaws; tool-specific rules.
  - **Tools**: SonarQube, Checkmarx, Fortify.
- **DAST**:
  - **Pros**: Tests real-world attack vectors.
  - **Cons**: Requires running applications; may miss logic errors.
  - **Tools**: OWASP ZAP, Burp Suite, Acunetix.

### **3. Penetration Testing**
- **Scope**: Define boundaries (e.g., internal networks, public-facing APIs).
- **Phases**:
  1. **Reconnaissance**: Gather public/private intel (e.g., whois, port scans).
  2. **Vulnerability Scanning**: Use tools like **Nessus** or **OpenVAS**.
  3. **Exploitation**: Simulate attacks (e.g., Metasploit, Cobalt Strike).
  4. **Post-Exploitation**: Assess impact (e.g., data exposure, lateral movement).
  5. **Reporting**: Prioritize findings (CVSS scoring); include remediation steps.
- **Legal**: Ensure **written authorization** (e.g., signed agreements).

### **4. Dependency Scanning**
- **Automation**: Integrate with build pipelines (e.g., GitHub Actions, Jenkins).
- **Example Workflow**:
  ```yaml
  # Example GitHub Actions step for dependency scanning
  - name: Scan dependencies
    uses: actions/github-script@v6
    with:
      script: |
        const { execSync } = require('child_process');
        execSync('npm audit --audit-level=critical');
  ```
- **Tools**: Snyk, Dependabot, OWASP Dependency-Check.

### **5. Continuous Security Monitoring**
- **SIEM Integration**: Forward logs to **Splunk**, **ELK Stack**, or **Microsoft Sentinel**.
- **Key Metrics**:
  - **Mean Time to Detect (MTTD)**: < 10 minutes for critical alerts.
  - **False Positive Rate**: < 5% (adjust thresholds accordingly).
- **Tools**: Wazuh, Graylog, Datadog.

### **6. Compliance Testing**
- **Standards**:
  - **OWASP Top 10**: Prioritize against common web app vulnerabilities.
  - **PCI-DSS**: For payment systems (e.g., encryption, tokenization).
  - **GDPR**: For EU data protection (e.g., right to erasure, breach notifications).
- **Automation**: Use **Policy-as-Code** (e.g., Open Policy Agent) for infrastructure compliance.

### **7. Secure Coding Guidelines**
- **Input Validation**: Sanitize all user inputs (e.g., regex for emails, escaping HTML).
- **Example (Python)**:
  ```python
  import re
  def validate_email(email):
      if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
          raise ValueError("Invalid email format")
  ```
- **Secrets Management**: Use **environment variables** or **vaults** (e.g., AWS Secrets Manager) for API keys.
- ** Principals**: Follow **OWASP Cheat Sheets** (e.g., [Secure Coding Guidelines](https://cheatsheetseries.owasp.org/)).

---

## **Query Examples**

### **1. SAST Scan Integration (SonarQube CLI)**
```bash
# Run SAST scan and publish results to SonarQube
sonar-scanner \
  -Dsonar.projectKey=my_app \
  -Dsonar.sources=src \
  -Dsonar.login=$SONAR_TOKEN
```

### **2. DAST Scan (OWASP ZAP)**
```bash
# Start ZAP CLI with a target URL
zap-cli quick-scan -t https://example.com -r zap-report.html
```

### **3. Dependency Scan (Snyk)**
```bash
# Scan npm dependencies for vulnerabilities
snyk test --severity-threshold=high
```

### **4. SQL Injection Test (Burp Suite)**
1. Open **Burp Suite** → **Proxy** → Intercept requests.
2. Modify a query parameter to test:
   ```
   GET /login?id=1' OR '1'='1 HTTP/1.1
   ```
3. Analyze responses for errors (e.g., SQL syntax errors).

### **5. Cloud Configuration Scan (AWS Config)**
```bash
# Use AWS CLI to check for non-compliant resources
aws configservice list-discovered-resources --resource-type ec2-instance
```

### **6. Phishing Simulation (KnowBe4)**
```json
# API request to trigger a phishing campaign (example payload)
{
  "campaign": {
    "name": "Security Awareness Test",
    "email_template": "phishing_test.html",
    "recipients": ["user1@example.com", "user2@example.com"],
    "schedule": "NOW"
  }
}
```

---

## **Related Patterns**

| **Pattern**               | **Relationship to Security Testing**                                                                 | **When to Use Together**                          |
|---------------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **DevSecOps**             | Integrates security into CI/CD pipelines.                                                          | Run SAST/DAST in every build; automate remediation. |
| **Compliance Testing**    | Validates adherence to standards (e.g., ISO 27001).                                                | Conduct annual compliance audits alongside security tests. |
| **Performance Testing**   | Ensures applications remain secure *and* performant under load.                                      | Test for DoS vulnerabilities during load tests.     |
| **API Testing**           | Focuses on securing APIs (e.g., OAuth, JWT validation).                                           | Use DAST tools to scan API endpoints for flaws.     |
| **Infrastructure as Code (IaC)** | Applies security to cloud configurations (e.g., Terraform policies).                          | Scan IaC templates for misconfigurations pre-deployment. |
| **Incident Response**     | Defines actions after a security breach is detected.                                                | Use monitoring alerts to trigger incident workflows. |
| **Vulnerability Management** | Tracks and prioritizes fixes for vulnerabilities.                                                  | Log findings from penetration tests in a vulnerability database. |

---

## **Key Takeaways**
1. **Start Early**: Embed security testing in **design, development, and deployment**.
2. **Automate**: Integrate tools into **CI/CD** (SAST/DAST) and **infrastructure** (IaC scanning).
3. **Test Realistically**:
   - Use **DAST** for runtime flaws.
   - Simulate **penetration tests** quarterly.
4. **Monitor Continuously**: Deploy **SIEM** and **log analysis** for real-time threats.
5. **Educate Teams**: Train developers on **secure coding** and security awareness.
6. **Comply**: Align tests with **regulatory requirements** (e.g., GDPR, HIPAA).

---
**Next Steps**:
- [OWASP Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/cis-controls/)