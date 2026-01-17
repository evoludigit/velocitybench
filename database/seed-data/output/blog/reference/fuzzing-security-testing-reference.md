---
# **[Pattern] Fuzzing & Security Testing – Reference Guide**

## **Overview**
Fuzzing and security testing is a proactive approach to uncovering vulnerabilities, bugs, and security flaws in software, APIs, protocols, or infrastructure. This pattern provides a structured methodology for implementing automated and manual security assessments, covering fuzzing techniques (e.g., differential, mutation, and generational fuzzing), static/dynamic analysis, and security scanning. Best practices include defining test scope, prioritizing risks, and integrating security testing into CI/CD pipelines for continuous validation.

---

## **Schema Reference**
The following table outlines core components of the **Fuzzing & Security Testing** pattern:

| **Component**               | **Description**                                                                                     | **Key Attributes**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Target System**           | The application, service, or infrastructure under test (e.g., web app, API, network protocol).    | - Target Type (e.g., Web, Mobile, IoT, Network)                                                      |
|                                 |                                                                                                     | - Environment (Dev, Staging, Production)                                                              |
|                                 |                                                                                                     | - Version, Build, or Commit ID                                                                          |
| **Fuzzing Technique**        | Method of generating malicious or malformed inputs.                                                   | - **Mutation**: Randomly alters valid inputs to create variations.                                     |
|                                 |                                                                                                     | - **Generational**: Creates synthetic inputs from scratch.                                             |
|                                 |                                                                                                     | - **Differential**: Uses multiple fuzzers to generate inputs, comparing outputs for inconsistencies.  |
|                                 |                                                                                                     | - **Coverage-Guided**: Directs fuzzing based on code coverage to uncover untested paths.              |
| **Test Inputs**              | Sources of fuzz test cases (e.g., dictionaries, protocols, user-generated data).                    | - Input Type (e.g., HTTP requests, files, network packets)                                         |
|                                 |                                                                                                     | - Seed Corpus (initial inputs for mutation)                                                          |
|                                 |                                                                                                     | - Custom Payloads (e.g., SQLi, XSS vectors)                                                           |
| **Tooling**                  | Software and frameworks for executing tests.                                                         | - **Static Analysis**: Bandit, SonarQube, Checkmarx                                                   |
|                                 |                                                                                                     | - **Dynamic Analysis**: AFL (American Fuzzy Lop), libFuzzer, Burp Suite                              |
|                                 |                                                                                                     | - **Network Scanners**: Nmap, Masscan, Burp Scanner                                                    |
|                                 |                                                                                                     | - **Web App Scanners**: OWASP ZAP, Squidgy                                                             |
| **Test Scope**               | Defines boundaries of the assessment (e.g., OWASP Top 10 categories, custom risk priorities).      | - Focus Areas (e.g., Injection, Broken Auth, CSRF)                                                   |
|                                 |                                                                                                     | - Exclusions (e.g., third-party dependencies, legacy systems)                                       |
| **Execution Environment**    | Infrastructure and setup for running tests.                                                         | - Containerized (Docker, Kubernetes)                                                                 |
|                                 |                                                                                                     | - Isolated (Virtual Machines, sandboxed)                                                              |
|                                 |                                                                                                     | - CI/CD Integration (GitHub Actions, Jenkins)                                                        |
| **Results & Reporting**      | Outputs and metrics from fuzzing sessions.                                                            | - Crash Reports (core dumps, stack traces)                                                          |
|                                 |                                                                                                     | - Vulnerability Severity (Critical, High, Medium, Low)                                               |
|                                 |                                                                                                     | - Coverage Metrics (e.g., % of code executed)                                                       |
| **Remediation & Fix Validation** | Process for addressing findings and verifying fixes.                                                  | - Patch Validation (re-fuzz to confirm resolution)                                                   |
|                                 |                                                                                                     | - Risk Acceptance (if exploits are deemed impractical or low-risk)                                   |

---

## **Implementation Details**

### **1. Defining the Test Scope**
- **Objective**: Align testing with business and security priorities.
- **Steps**:
  1. **Identify Assets**: Document all components (e.g., APIs, services, databases) exposed to external traffic.
  2. **Risk Prioritization**: Use frameworks like **OWASP Top 10** or **MITRE ATT&CK** to categorize risks.
  3. **Exclusions**: Exclude non-critical systems or third-party dependencies unless explicitly required.
  4. **Compliance**: Ensure alignment with regulations (e.g., PCI DSS, GDPR, HIPAA).

**Example Scope Definition**:
```
Scope: REST API (v1.2.0) exposed via `/api/*` endpoints.
Focus: Injection (SQLi, NoSQLi), Broken Authentication, Security Misconfigurations.
Exclusions: Internal services (localhost:8080), third-party payment gateway.
```

---

### **2. Selecting Fuzzing Techniques**
Choose techniques based on the target system and vulnerability surface:

| **Technique**          | **Use Case**                                                                                     | **Tools**                                  |
|------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------|
| **Mutation Fuzzing**   | Ideal for structured inputs (e.g., JSON, XML).                                                | AFL++, libFuzzer                           |
| **Generational Fuzzing** | Best for unstructured protocols (e.g., HTTP headers, network packets).                         | Boofuzz, Radamsa                          |
| **Differential Fuzzing** | Compares outputs of multiple fuzzers to find inconsistencies.                                  | HTTPFuzz + Burp Suite                     |
| **Coverage-Guided**    | Maximizes code coverage by prioritizing untested paths.                                         | AFL++, Honggfuzz                           |
| **Web App Fuzzing**    | Targets web applications (e.g., parameter tampering, XSS, CSRF).                              | OWASP ZAP, Burp Suite                     |

---

### **3. Preparing Test Inputs**
- **Seed Corpus**: Start with valid inputs (e.g., sample API requests, protocol specifications).
- **Custom Payloads**: Craft malicious inputs based on known vulnerabilities (e.g., SQLi: `' OR 1=1 --`).
- **Dictionaries**: Use wordlists for brute-forcing (e.g., `SecLists`, `CVE databases`).
- **Protocol Knowledge**: Understand the target’s grammar (e.g., HTTP headers, SQL syntax).

**Example Seed Corpus for REST API**:
```json
// Valid request (seed)
{
  "seed": {
    "id": "123",
    "action": "GET",
    "headers": {"Authorization": "Bearer valid_token"}
  }
}

// Malicious input (mutation)
{
  "malicious": {
    "id": "123' OR '1'='1",
    "action": "DELETE",
    "headers": {"Authorization": ""} // Missing token
  }
}
```

---

### **4. Tooling Setup**
#### **Static Analysis (SAST)**
- **Tools**: SonarQube, Checkmarx, Bandit (Python), Semgrep.
- **How to Use**:
  1. Integrate into CI/CD (e.g., scan before merge).
  2. Configure rules for your tech stack (e.g., Java, Node.js, Go).
  3. Generate reports with severity ratings.

#### **Dynamic Analysis (DAST/Fuzzing)**
- **Tools**: AFL++, libFuzzer (C/C++), Boofuzz (Python), OWASP ZAP.
- **How to Use**:
  1. **Containerize the Target**: Run fuzzing in isolated environments (Docker).
  2. **Monitor for Crashes**: Use crash handlers (e.g., `AFL's coredump`).
  3. **Analyze Coverage**: Tools like `llvm-cov` help track untested code.

**Example AFL++ Command**:
```bash
./afl-fuzz -i ./input_dir -o ./output_dir ./target_program @@@
```

#### **Network/Protocol Fuzzing**
- **Tools**: Scapy, Boofuzz, Wireshark.
- **How to Use**:
  1. Craft custom packets (e.g., HTTP, DNS).
  2. Use **Scapy** to modify headers/fields dynamically:
     ```python
     from scapy.all import *
     payload = "A" * 1000
     packet = IP(dst="192.168.1.1") / TCP(dport=80) / payload
     send(packet)
     ```

---

### **5. Running Fuzzing Sessions**
- **Automated Workflow**:
  1. **Seed Phase**: Start with valid inputs.
  2. **Mutation/Generation Phase**: Apply fuzzing techniques.
  3. **Crash Collection**: Capture core dumps or error logs.
  4. **Analysis**: Review crashes for vulnerabilities (e.g., segfaults, buffer overflows).
- **Manual Testing**: Use **Burp Suite** or **OWASP ZAP** for interactive inspection.

**Example CI/CD Integration (GitHub Actions)**:
```yaml
name: Fuzz Test
on: [push]
jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup AFL
        run: sudo apt-get install afl
      - name: Run Fuzzer
        run: afl-fuzz -i seeds/ -o results/ ./target
```

---

### **6. Analyzing Results**
- **Crash Reports**: Use tools like `gdb` or `strace` to analyze core dumps.
- **Vulnerability Triaging**:
  - **Critical**: Remote code execution (RCE), arbitrary write.
  - **High**: SQLi, Command Injection, XSS.
  - **Medium**: Improper error handling, insecure direct object references (IDOR).
- **Severity Scoring**: Use **CVSS** (Common Vulnerability Scoring System) for risk assessment.

**Example Crash Analysis**:
```
*** Crash detected at: 0x40123456
Buffer overflow in parse_request() at line 42.
Input: "GET /admin?id=1; DROP TABLE users;--"
```

---

### **7. Remediation & Validation**
- **Fixing Vulnerabilities**:
  - **Code Changes**: Apply patches (e.g., input sanitization, rate limiting).
  - **Configuration**: Harden defaults (e.g., disable debug modes, enforce HTTPS).
- **Re-Fuzzing**: Run tests again to confirm resolution:
  ```bash
  ./afl-fuzz -i seeds/ -o results_patched/ ./target_patched
  ```
- **Risk Acceptance**: Document justified exclusions (e.g., "Vulnerability exploitable only in lab").

---

## **Query Examples**
### **1. How do I fuzz a REST API with Boofuzz?**
```
# Install Boofuzz
pip install boofuzz

# Define a simple fuzzable HTTP request
from boofuzz import *

session = Session(target=Target(connection=SocketConnection("192.168.1.100", 80)))
session.session_param("id", "123")  # Parameter to fuzz
session.param("id", "123' OR '1'='1")  # Custom payload

# Add a fuzzer
session.fuzz()
session.attach(feedback_modules=[CrashFeedback()])
```

### **2. How to configure AFL++ for C code?**
```
# Compile target with AFL instrumentation
gcc -o target -fPIC -g -O0 -I/usr/include/afl target.c

# Run fuzzer with input directory
afl-fuzz -i /path/to/seeds/ -o /path/to/output/ ./target @@
```

### **3. What’s the difference between mutation and generational fuzzing?**
| **Mutation**               | **Generational**                          |
|----------------------------|-------------------------------------------|
| Takes valid inputs and alters them (e.g., bit-flipping). | Generates inputs from scratch (e.g., random strings). |
| Works well for structured formats (JSON, XML).           | Better for unstructured protocols (e.g., raw HTTP headers). |
| Example: AFL, libFuzzer.                                   | Example: Boofuzz, Radamsa.                |

### **4. How to integrate security testing into CI/CD?**
Use a pipeline like this:
1. **SAST Scan**: Run on every PR (e.g., SonarQube).
2. **DAST/Fuzzing**: Run on merge to `main` (e.g., GitHub Actions + AFL).
3. **Manual Review**: Flag high-risk findings for triage.
4. **Reporting**: Generate a dashboard (e.g., Grafana + Prometheus).

**Example Jenkins Pipeline**:
```groovy
pipeline {
    agent any
    stages {
        stage('SAST') {
            steps { sh 'sonarqube-scanner' }
        }
        stage('DAST') {
            steps { sh './run_fuzzer.sh' }
        }
        stage('Report') {
            steps { junit '**/results/*.xml' }
        }
    }
}
```

---

## **Related Patterns**
1. **[Security Compliance Checks]** – Ensure adherence to standards (e.g., PCI DSS, ISO 27001).
2. **[Dependency Scanning]** – Identify vulnerable third-party libraries (e.g., GitHub Dependabot, Snyk).
3. **[Incident Response]** – Handle discovered vulnerabilities post-discovery.
4. **[Code Review Guidelines]** – Enforce security best practices in pull requests.
5. **[Threat Modeling]** – Proactively identify attack vectors before testing.
6. **[Penetration Testing]** – Manual exploitation testing for critical systems.
7. **[Performance Testing]** – Ensure security testing doesn’t degrade system performance.