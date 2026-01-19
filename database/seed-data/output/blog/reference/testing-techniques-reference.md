# **[Pattern] Testing Techniques Reference Guide**
*Structured methods for validating software quality*

---

## **Overview**
The **Testing Techniques** pattern provides a framework of well-defined methods to systematically evaluate software components, ensuring correctness, reliability, and compliance. This guide categorizes techniques by purpose (e.g., functional, non-functional, structural) and outlines their use cases, prerequisites, and execution workflows. Techniques range from foundational (e.g., unit testing) to advanced (e.g., model-based testing), enabling teams to select appropriate strategies based on project goals, constraints, and risks.

Key principles include:
- **Purpose-driven selection** (e.g., test for requirements, design flaws, or performance bottlenecks).
- **Automation readiness** (identify techniques with high reusability potential).
- **Traceability** (link tests to requirements, code, or user flows).
- **Risk-based prioritization** (focus effort where defects cause the most impact).

---

## **Schema Reference**
The following tables categorize testing techniques by type, scope, and technical characteristics.

### **1. Technique Classification**
| **Category**          | **Subcategory**               | **Purpose**                                                                 | **Scope**               | **Key Tools**                          |
|-----------------------|--------------------------------|-----------------------------------------------------------------------------|-------------------------|----------------------------------------|
| **Functional**        | Unit Testing                  | Validate small code units (e.g., functions, classes).                      | Code-level              | JUnit, pytest, NUnit                   |
|                       | Integration Testing           | Test interactions between components/modules.                              | Component-level         | Mocking tools, Docker, Selenium       |
|                       | System Testing                | Verify system-wide functionality against requirements.                      | System-level            | CI/CD pipelines, LoadRunner            |
|                       | End-to-End (E2E) Testing       | Test complete user flows (e.g., checkout process).                          | User journey            | Cypress, Playwright, TestComplete      |
| **Non-Functional**    | Performance Testing           | Assess speed, scalability, and resource usage under load.                   | Infrastructure         | JMeter, Gatling, LoadRunner            |
|                       | Security Testing              | Identify vulnerabilities (e.g., SQL injection, auth bypass).               | Code/infrastructure    | OWASP ZAP, Burp Suite, SonarQube      |
|                       | Usability Testing             | Evaluate user experience (UX) and accessibility.                          | UI/UX                   | UserTesting, Hotjar, Maze              |
|                       | Localization Testing          | Validate software in multiple languages/cultures.                          | Internationalization    | Crowdin, Localazy                       |
| **Structural**        | Static Analysis               | Analyze code for bugs, anti-patterns, or compliance (without execution).   | Code                    | SonarQube, ESLint, Checkstyle          |
|                       | Mutation Testing              | Inject faults to measure test suite robustness.                             | Test suite              | PIT, MutPy, Stryker                     |
|                       | Property-Based Testing        | Generate test cases from mathematical properties (e.g., "all inputs ≥ 0"). | Code/algorithm          | Hypothesis, QuickCheck                 |
| **Exploratory**       | Ad-Hoc Testing                | Unscripted testing by manual execution to uncover edge cases.              | Any                     | Manual, session recording tools        |
|                       | Pair Testing                  | Collaborative testing where two testers work together.                     | Team-level              | Shared workspaces, whiteboard tools    |
| **Regression**        | Smoke Testing                 | Quick sanity checks for critical features post-deploy.                     | Critical paths          | CI gate scripts                         |
|                       | Regresssion Suites            | Automated retesting of changed components.                                 | Component/system        | Test automation frameworks              |
|                       | Delta Testing                 | Compare current behavior vs. baseline (e.g., after code changes).         | System                  | Diff tools, version control (Git)     |

---

### **2. Technique Attributes**
| **Attribute**         | **Description**                                                                 |
|-----------------------|---------------------------------------------------------------------------------|
| **Automation Level**  | Manual (🔹), Partial (🔹🔹), Fully Automated (🔹🔹🔹)                                  |
| **Coverage**          | Code (e.g., branch, statement), Requirements, Risk-based, Usage-based          |
| **Dependency**        | Standalone (✅), Requires Mocks (⚠️), Requires Infrastructure (🚧)               |
| **Maintenance**       | Low (🟢), Moderate (🟡), High (🔴)                                                   |
| **Detection Depth**   | Shallow (bugs in UI), Deep (logic/algorithm flaws)                             |

---

## **Query Examples**
Use these templates to select techniques based on project needs.

### **1. Selecting Techniques by Scope**
**Goal:** Identify techniques to test a microservice API.
**Query:**
```sql
SELECT * FROM techniques
WHERE scope = 'component-level'
  AND category IN ('Functional', 'Non-Functional')
  AND automation_level IN ('🔹🔹', '🔹🔹🔹')
  AND "Dependency" NOT LIKE '%🚧%';
```
**Expected Output:**
- Integration Testing (API endpoints)
- Performance Testing (latency under load)
- Static Analysis (API contract validation)

---

### **2. Risk-Based Technique Selection**
**Goal:** Prioritize techniques for a high-risk system (e.g., healthcare).
**Query:**
```sql
SELECT technique, purpose
FROM techniques
WHERE category = 'Non-Functional'
  AND technique IN ('Security Testing', 'Usability Testing', 'Localization Testing')
ORDER BY impact_score DESC;
```
**Expected Output:**
1. **Security Testing** (Critical for patient data)
2. **Usability Testing** (Avoids clinician errors)
3. **Localization Testing** (Multilingual compliance)

---

### **3. Automation-Friendly Techniques**
**Goal:** Find techniques suitable for CI/CD pipelines.
**Query:**
```sql
SELECT technique, automation_level, maintenance
FROM techniques
WHERE automation_level = '🔹🔹🔹'
  AND maintenance IN ('🟢', '🟡');
```
**Expected Output:**
- Unit Testing (🔹🔹🔹, Low maintenance)
- Integration Testing (🔹🔹🔹, Moderate maintenance)
- Regression Suites (🔹🔹🔹, Low maintenance)

---

## **Implementation Workflow**
### **1. Pre-Testing Setup**
- **Define Scope:**
  - Map techniques to requirements (e.g., use *System Testing* for user stories).
  - Identify critical paths (e.g., payment flows) for *Smoke Testing*.
- **Toolchain:**
  - Pair techniques with tools (e.g., *Property-Based Testing* → Hypothesis).
  - Integrate with CI/CD (e.g., run *Regression Suites* on every pull request).
- **Data Preparation:**
  - For *Performance Testing*, simulate production load using synthetic users.
  - For *Localization Testing*, populate test data in target languages.

### **2. Execution**
| **Technique**          | **Execution Steps**                                                                 | **Output**                          |
|------------------------|------------------------------------------------------------------------------------|-------------------------------------|
| **Unit Testing**       | Write assertions for code units; run in IDE or CI.                                 | Pass/Fail status, coverage reports  |
| **Mutation Testing**   | Instrument test suite; inject mutations; measure test failure rate.               | Mutation score (e.g., 90% killed)  |
| **Exploratory Testing**| Testers manually explore app; document bugs.                                       | Bug reports, session recordings     |
| **Performance Testing**| Deploy test environment; simulate load; monitor metrics (latency, errors).       | Load test reports, thresholds        |

### **3. Post-Testing**
- **Analysis:**
  - Compare *Mutation Testing* scores across sprints to track test suite robustness.
  - Use *Delta Testing* to validate regression fixes.
- **Reporting:**
  - Generate dashboards linking *Security Testing* findings to vulnerabilities.
  - Highlight *Usability Testing* pain points in user feedback loops.
- **Optimization:**
  - Refactor low-coverage areas in *Static Analysis* reports.
  - Update *Property-Based* test cases if new edge cases emerge.

---

## **Query Examples (Practical Scenarios)**
### **Scenario 1: Mobile App Launch**
**Goal:** Ensure app meets pre-launch standards.
**Query:**
```markdown
1. **Functional:**
   - End-to-End Testing (🔹🔹🔹): Validate on-screen workflows (e.g., login → dashboard).
   - Usability Testing (🔹): Test with real users; prioritize accessibility.

2. **Non-Functional:**
   - Performance Testing (🔹🔹🔹): Simulate 10K concurrent users; target <500ms response.
   - Localization Testing (🔹): Test UI strings in 5 languages.

3. **Regression:**
   - Smoke Testing (🔹🔹): Quick check of critical features post-update.
```

**Tools:**
- E2E: Appium + Selenium
- Performance: JMeter
- Usability: UserTesting

---

### **Scenario 2: Legacy System Refactor**
**Goal:** Validate changes without breaking existing functionality.
**Query:**
```markdown
1. **Structural:**
   - Static Analysis (🔹🔹): Scan for deprecated APIs or security flaws.
   - Mutation Testing (🔹): Validate test suite catches refactoring bugs.

2. **Regression:**
   - Delta Testing (🔹): Compare new build vs. baseline (e.g., database schema).
   - Regresssion Suites (🔹🔹🔹): Automated retest of changed modules.

3. **Exploratory:**
   - Pair Testing (🔹): Developers + testers manually explore new features.
```

**Tools:**
- Static Analysis: SonarQube
- Mutation Testing: PIT
- Delta Testing: Git diff + custom scripts

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **How They Interact**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **[Test Pyramid](link)**  | Structure tests by level (unit > integration > E2E) to optimize effort.         | Use *Testing Techniques* to populate each layer (e.g., unit tests = Unit Testing).  |
| **[Behavior-Driven Dev](link)** | Write tests in Gherkin (Given-When-Then) for collaboration.             | *Functional Techniques* (e.g., E2E) can be implemented from BDD scenarios.          |
| **[Risk-Based Testing](link)** | Prioritize tests based on impact/likelihood of failure.                       | *Testing Techniques* are selected/weighted by risk (e.g., Security Testing for PII). |
| **[Continuous Testing](link)** | Integrate testing into the DevOps pipeline.                                | Automate *Regression Suites*, *Smoke Testing*, and *Performance Testing* in CI.     |
| **[Contract Testing](link)** | Validate interactions between services via OpenAPI/Swagger.                 | Use *Integration Testing* to enforce API contracts (e.g., Postman/Newman).           |

---

## **Anti-Patterns to Avoid**
1. **Over-Reliance on E2E Testing:**
   - *Problem:* Slow, brittle, and expensive to maintain.
   - *Fix:* Combine with *Unit* and *Integration Testing* (follow the Test Pyramid).

2. **Neglecting Non-Functional Tests:**
   - *Problem:* Slow, memory-leaky apps pass functional tests but fail in production.
   - *Fix:* Include *Performance Testing* early; use *Security Testing* for critical systems.

3. **Manual Exploratory Testing Without Documentation:**
   - *Problem:* Inconsistent findings; hard to reproduce.
   - *Fix:* Record sessions and link bugs to *Smoke* or *Regression Suites*.

4. **Ignoring Mutation Testing:**
   - *Problem:* False confidence in test suite quality.
   - *Fix:* Run *Mutation Testing* periodically; aim for >80% kill rate.

5. **Static Analysis as a One-Time Check:**
   - *Problem:* Debt accumulates; new code is unclean.
   - *Fix:* Integrate *Static Analysis* into CI with strict rules (e.g., fail builds on critical issues).

---
## **Further Reading**
- **Books:**
  - *Testing Computer Software* by Glenford Myers (foundational techniques).
  - *Lessons in Test-Driven Development* by James Grenning (practical TDD).
- **Standards:**
  - ISO/IEC 25010: Quality models for software.
  - ISTQB Glossary: Official testing terminology.
- **Tools:**
  - [Test Automation Frameworks Comparison](https://www.testautomationuap.com/)
  - [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) (security).