---
# **[Pattern] Waterfall Practices: Reference Guide**

---

## **Overview**
The **Waterfall Practices** pattern is a structured, sequential approach to software development and project execution where each phase must be completed before the next begins. Unlike iterative or agile methodologies, this pattern follows a linear workflow, ensuring clear delivery milestones, regulatory compliance, and predictability for projects with stable requirements. It excels in domains like **construction, regulatory-constrained industries (e.g., healthcare, aerospace), and documentation-heavy projects** where risk mitigation and traceability are critical. Key phases include **Requirements, Design, Implementation, Verification, and Maintenance**, each with predefined deliverables and gate reviews. Organizations adopt this pattern to enforce discipline, enforce stakeholder sign-off, and simplify audit processes. Best suited for projects where requirements are well-defined upfront and scope changes are minimal, Waterfall Practices minimize rework but may lead to inflexibility if requirements evolve.

---

## **Implementation Details**

### **Core Principles**
1. **Sequential Phases**: Each phase depends entirely on completion of the prior one.
2. **Documentation-Heavy**: Formal artifacts (e.g., SRS, test plans) must exist before phase progression.
3. **Gate Reviews**: Stakeholders approve deliverables at phase transitions; no backtracking allowed.
4. **Predictability**: Budgets and timelines are fixed post-phase 1 (Requirements).
5. **Risk Mitigation**: Early-stage validation reduces late-stage failures.

### **Phase Breakdown**
| Phase               | Purpose                                                                 | Key Deliverables                                                                 |
|---------------------|--------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Requirements**    | Define scope, constraints, and success criteria.                          | SRS (Software Requirements Specification), stakeholder agreement letter.        |
| **Design**          | Architect system components and interfaces.                                | High-level/low-level design docs, diagrams, class specifications.                 |
| **Implementation**  | Develop code/modules based on design.                                     | Source code, unit test cases, build artifacts.                                    |
| **Verification**    | Validate compliance with requirements (testing + reviews).               | Test reports, bug fixes, sign-off certificates.                                   |
| **Maintenance**     | Fix defects and implement minor scope changes.                           | Patch releases, change logs, updated documentation.                              |

### **When to Use**
✅ **Use Waterfall Practices when:**
- Requirements are **stable and well-understood**.
- Compliance/audit trails are **critical** (e.g., FDA, ISO 26262).
- Project **scope is fixed** (e.g., custom software for a defined process).
- Resources are **limited or constrained** (e.g., government contracts).

❌ **Avoid Waterfall Practices when:**
- Requirements are **unclear or volatile** (e.g., startups, research projects).
- Fast iteration is **required** (e.g., MVP development, SaaS).
- Stakeholder feedback is **essential early** (e.g., UX-driven products).

---

## **Schema Reference**
Below is a **schema table** for tracking Waterfall Practices implementation:

| **Field**            | **Description**                                                                 | **Example Value**                          | **Validation Rules**                     |
|----------------------|-------------------------------------------------------------------------------|--------------------------------------------|-------------------------------------------|
| `project_id`         | Unique identifier for the project.                                            | `PRJ-2024-001`                             | UUID or alphanumeric format.             |
| `phase`              | Current phase in the workflow (enum: `reqs`, `design`, `impl`, `verify`, `maintenance`). | `"design"`                                 | Must match schema values.                 |
| `start_date`         | Phase kickoff date (ISO 8601 format).                                         | `"2024-05-15"`                            | `YYYY-MM-DD` format.                      |
| `end_date`           | Phase completion date (nullable if in progress).                              | `"2024-07-30"` (or `null`)                | Must be ≥ `start_date`.                  |
| `deliverables`       | Array of objects describing phase outputs.                                     | `[{"name": "SRS_v1.0", "status": "approved"}]` | Must include `"status"` (e.g., `draft`, `reviewed`, `approved`). |
| `gate_review_score` | Numerical score (0–100) from stakeholder review.                              | `92`                                      | Integer between 0 and 100.                |
| `dependencies`       | List of tasks blocking phase progression.                                     | `[{"task_id": "TASK-002", "status": "pending"}]` | Task IDs must reference a tracking system. |

**Example JSON Payload:**
```json
{
  "project_id": "PRJ-2024-001",
  "phase": "verify",
  "start_date": "2024-08-01",
  "end_date": null,
  "deliverables": [
    {
      "name": "Integration_Test_Report_v1.0",
      "status": "approved",
      "version": "1.0",
      "reviewer": "QA-Lead"
    }
  ],
  "gate_review_score": 95,
  "dependencies": []
}
```

---

## **Query Examples**
Use these queries to **track progress**, **identify bottlenecks**, or **audit compliance** in a database/system storing Waterfall Practices data.

### **1. List All Projects in a Phase**
**Purpose**: Identify active projects in the `design` phase.
**Query**:
```sql
SELECT project_id, phase, start_date, end_date
FROM waterfall_projects
WHERE phase = 'design' AND end_date IS NULL
ORDER BY start_date DESC;
```

### **2. Find Projects with Low Gate Scores**
**Purpose**: Flag projects risking phase approval due to low stakeholder scores.
**Query**:
```sql
SELECT project_id, phase, gate_review_score
FROM waterfall_projects
WHERE gate_review_score < 80
ORDER BY gate_review_score ASC;
```

### **3. Track Deliverable Status by Phase**
**Purpose**: Generate a dashboard of "approved" vs. "draft" deliverables per phase.
**Query**:
```sql
SELECT
    phase,
    COUNT(CASE WHEN status = 'approved' THEN 1 END) AS approved_count,
    COUNT(CASE WHEN status = 'draft' THEN 1 END) AS draft_count
FROM waterfall_deliverables
GROUP BY phase;
```

### **4. Identify Delayed Phases**
**Purpose**: Alert teams to phases exceeding their estimated duration.
**Query**:
```sql
SELECT
    project_id,
    phase,
    start_date,
    end_date,
    DATEDIFF(CURRENT_DATE, end_date) AS days_overdue
FROM waterfall_projects
WHERE end_date < CURRENT_DATE
ORDER BY days_overdue DESC;
```

### **5. Extract Compliance-Audit Path**
**Purpose**: Generate a timeline of sign-offs for regulatory audits.
**Query**:
```sql
SELECT
    p.project_id,
    p.phase,
    p.start_date,
    d.name AS deliverable,
    d.status,
    d.reviewer,
    d.review_date
FROM waterfall_projects p
JOIN waterfall_deliverables d ON p.project_id = d.project_id
WHERE p.phase IN ('verify', 'maintenance')
ORDER BY p.project_id, d.review_date DESC;
```

---

## **Related Patterns**
| **Pattern**               | **Relationship to Waterfall Practices**                                                                 | **Use Case Synergy**                                                                 |
|---------------------------|--------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Big Bang Release**      | Often paired with Waterfall for **final deployment** after phase completion.                               | Ideal for legacy systems or projects with no iterative components.                   |
| **V-Shaped Model**        | Subset of Waterfall where **testing phases mirror development** (e.g., unit tests → system tests).    | Enhances verification rigor in safety-critical projects (e.g., automotive).          |
| **Agile Hybrid (Agile+Waterfall)** | Uses Waterfall for **core phases** (e.g., requirements) + Agile for **maintenance**.                | Balances stability and adaptability (e.g., government contracts with evolving needs). |
| **Phase-Gate Process**    | Extends Waterfall with **formalized decision gates** (e.g., Go/No-Go reviews).                          | Critical for R&D-heavy industries (e.g., pharma).                                      |
| **Documentation-Driven Development (DDD)** | Emphasizes **heavy documentation** like Waterfall but decouples it from linear phases.              | Useful for open-source projects or documentation-first workflows.                     |

---

## **Tools & Integrations**
| **Tool**               | **Purpose**                                                                 | **How It Supports Waterfall**                                                                 |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Jira (with Workflows)** | Task tracking and phase gates.                                            | Configure custom **Waterfall workflows** (e.g., "Blocked on Design Review").               |
| **Confluence**         | Centralize phase documentation (SRS, test plans).                          | Link deliverables to Jira tickets for traceability.                                        |
| **Git + CI/CD (e.g., Jenkins)** | Code versioning and build verification.                                    | Enforce **release gates** (e.g., "Do not merge unless `unit_tests = passed`").           |
| **Microsoft Project**  | Gantt charts for timeline management.                                      | Visualize phase dependencies and critical paths.                                           |
| **Audacity (Audit Logging)** | Track changes for compliance.                                              | Log every phase transition with timestamps and sign-offs.                                  |
| **Notion/DocuWare**    | Secure document storage for deliverables.                                  | Version control for SRS, test reports, and approvals.                                      |

---
**Note**: For hybrid setups, combine Waterfall with **Agile sprints in the Maintenance phase** for iterative fixes. Use tools like **GitHub Projects** or **ClickUp** to bridge linear and iterative workflows.