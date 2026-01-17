# **[Pattern] Lean Practices Reference Guide**

---

## **Overview**
**Lean Practices** is a structured approach to optimizing workflows, reducing waste, and maximizing efficiency by eliminating non-value-adding activities. Originating from **Toyota’s Lean Manufacturing**, this pattern applies principles like **continuous improvement (Kaizen)**, **just-in-time (JIT) production**, and **customer focus** across software development, project management, and operational processes. By identifying and addressing **7 types of waste** (defects, overproduction, waiting, transport, inventory, motion, excess processing), teams can streamline operations, improve quality, and deliver faster with fewer resources.

This guide covers core Lean principles, implementation steps, schema references for workflows, and practical queries to apply Lean in various contexts. It is designed for **product managers, engineers, DevOps teams, and process owners** seeking to adopt a Lean mindset.

---

## **Key Concepts & Implementation Details**

### **1. Core Lean Principles**
| Principle               | Description                                                                 | Example in Software Dev                     |
|-------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **Customer Focus**      | Prioritize value from the customer’s perspective.                           | Agile sprints align with user stories       |
| **Value Stream Mapping**| Visualize workflows to identify waste.                                       | Trace code from commit to deployment       |
| **Just-in-Time (JIT)**  | Produce only what is needed, when needed.                                   | CI/CD pipelines trigger builds on pull requests |
| **Continuous Improvement (Kaizen)** | Small, iterative enhancements to processes.                          | Post-mortems and retrospectives              |
| **Respect for People**  | Empower teams to innovate and suggest improvements.                        | Cross-functional squads with autonomy       |
| **Eliminate Waste**     | Target the **7 Wastes** (see Schema Reference).                             | Reduce testing bottlenecks with automation |

### **2. The 7 Types of Waste**
| Waste Type               | Definition                                                                 | Lean Mitigation Strategies                     |
|--------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **Defects**              | Errors requiring rework or fixes.                                            | Shift-left testing, peer reviews              |
| **Overproduction**       | Creating unnecessary inventory or features.                                 | Backlog gating, feature toggles               |
| **Waiting**              | Idle time due to delays (e.g., approvals, dependencies).                    | Parallelize reviews, reduce hand-offs          |
| **Transport**            | Unnecessary movement of information/artifacts.                              | Single-source truth (e.g., shared docs)       |
| **Inventory**            | Excess work-in-progress (WIP) or unfinished tasks.                         | Limit WIP per team                            |
| **Motion**               | Inefficient workflow steps or manual processes.                             | Automate repetitive tasks (e.g., PR templates)|
| **Excess Processing**    | Unnecessary steps or complexity in workflows.                              | Simplify onboarding, reduce meetings          |

---

## **Schema Reference**
Below are **schema templates** for Lean workflows in different domains. Use these to model your processes.

### **1. Value Stream Mapping (VSM) Template**
| **Step**       | **Activity**               | **Owner**       | **Time** | **Waste Type** | **Next Step**          |
|----------------|----------------------------|-----------------|----------|------------------|------------------------|
| S1             | Requirement Gathering       | PM              | 2 days   | Waiting         | S2                     |
| S2             | Dev Sprint Planning         | Dev Lead        | 1 day    | Overproduction   | S3                     |
| S3             | Code Review (Manual)        | QA Engineer     | 3 days   | Defects/Waiting  | S4                     |
| S4             | Deployment (Manual)         | Ops             | 1 day    | Motion/Error     | Done                   |

**Key Metrics to Track:**
- **Cycle Time**: Time from start to finish (e.g., S1 → Done).
- **Throughput**: Tasks completed per sprint.
- **Waste %**: % of time spent on non-value-added activities.

---

### **2. Kanban Board Schema**
| **Column**       | **Definition**                          | **Lean Optimization Tips**                          |
|------------------|-----------------------------------------|---------------------------------------------------|
| **To Do**        | Ideas/Backlog items                     | Limit WIP to avoid multitasking                   |
| **In Progress**  | Active tasks                            | Color-code by priority (e.g., red=blocked)        |
| **Review**       | Waiting for feedback                    | Set SLAs for review cycles                        |
| **Done**         | Completed items                         | Celebrate small wins to reinforce Kaizen culture |

**Example Query (Jira/Kanban Tools):**
```sql
SELECT
    column,
    COUNT(*) AS task_count,
    AVG(age_in_days) AS avg_age
FROM kanban_board
GROUP BY column
ORDER BY avg_age DESC;
```
**Output Interpretation:**
- High `avg_age` in "In Progress" = bottlenecks (e.g., blocked tasks).
- Long "Review" queue = inefficient feedback loops.

---

### **3. CI/CD Pipeline Schema (Lean DevOps)**
```
[Push to Git] → [Build (Auto)] → [Test Suite (Parallel)] → [Deploy Staging] → [User Testing] → [Deploy Prod]
```
**Lean Adjustments:**
- **Eliminate Waste**: Skip staging if tests pass.
- **JIT Delivery**: Deploy only when PR is merged (no overproduction).
- **Respect for People**: Automate repetitive builds to reduce errors.

**Query Example (GitHub Actions Logs):**
```sql
SELECT
    branch,
    COUNT(CASE WHEN status = 'failure' THEN 1 END) AS failures,
    AVERTIME(time_to_finish, time_started) AS avg_failure_duration
FROM pipeline_runs
GROUP BY branch
HAVING failures > 0;
```

---

## **Query Examples**
### **1. Identify Waste in Project Backlog**
**Problem**: Backlog items sit stagnant for months.
**Query (Jira REST API):**
```bash
curl -X GET "https://your-domain.atlassian.net/rest/api/2/search?jql=status=Backlog&maxResults=1000" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```
**Lean Action**:
- Flag items with `age > 90 days` for prioritization.
- Use **Lean portfolio management** to cull low-value items.

---

### **2. Measure Process Waste in DevOps**
**Problem**: Deployments fail due to manual steps.
**Query (Prometheus Metrics):**
```promql
up{namespace="deployments"} * on() group_left(node) node_up
  unless (up{job="kubernetes-pods"} == 0)
```
**Lean Action**:
- Replace manual steps with **Golden Path CI/CD** (e.g., ArgoCD).
- Track **mean time to recover (MTTR)** post-failures.

---

### **3. Analyze Team Velocity (Kaizen Tracking)**
**Query (Linear/Bugzilla):**
```sql
SELECT
    sprint,
    COUNT(*) AS stories_completed,
    AVG(story_points) AS avg_points_per_sprint,
    SUM(CASE WHEN status = 'Blocked' THEN 1 ELSE 0 END) AS blocked_stories
FROM sprints
WHERE team = 'Frontend'
GROUP BY sprint
ORDER BY avg_points_per_sprint DESC;
```
**Lean Insight**:
- Declining `avg_points_per_sprint`? → Investigate blocked stories.
- High `blocked_stories` → Improve dependency management (e.g., sync with backend).

---

## **Requirements & Implementation Checklist**
| Step               | Action Items                                                                 | Tools/Metrics to Use                          |
|--------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **1. Map Value Streams** | Document end-to-end workflows (e.g., idea → production).                  | Miro, Lucidchart, VSM templates               |
| **2. Identify Waste**   | Audit each step against the **7 Wastes**.                                   | Time-tracking (Harvest), error logs           |
| **3. Set WIP Limits**  | Cap work-in-progress to avoid multitasking.                                | Kanban tools (Trello, ClickUp)                |
| **4. Automate Repetition** | Replace manual steps with scripts/bots.                                   | CI/CD (GitHub Actions), RPA (UiPath)          |
| **5. Gather Feedback**  | Conduct **quick Kaizen workshops** every 2 weeks.                           | Retrospective tools (Miro, Aha!)             |
| **6. Measure Impact**   | Track **cycle time reduction**, **defect rates**, and **team morale**.      | Dashboards (Grafana, Tableau)                 |

---

## **Related Patterns**
| Pattern Name            | Description                                                                 | When to Use                                                                 |
|-------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Agile Development**   | Iterative, incremental delivery in fixed-length sprints.                   | When prioritizing flexibility and customer feedback.                       |
| **DevOps**              | Culture of collaboration between Dev and Ops to streamline releases.        | For software teams aiming to reduce handoff delays.                         |
| **Continuous Delivery**| Automated, frequent deployments to production.                             | To achieve JIT software delivery.                                              |
| **Six Sigma**           | Data-driven process improvement to minimize defects.                      | For high-stakes processes with strict quality requirements.                 |
| **Scrumban**            | Hybrid of Scrum + Kanban for flexible workflows.                           | Teams needing structured sprints but with variable tasks.                    |
| **Total Quality Management (TQM)** | Holistic approach to quality across all organizational functions.      | When Lean alone isn’t enough for cross-functional quality.                  |

---

## **Antipatterns to Avoid**
| **Lean Antipattern**          | **Risk**                                                                   | **Mitigation Strategy**                              |
|--------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------|
| **"Lean as a checklist"**      | Blanket application without context; creates rigidity.                     | Tailor Lean to your team’s specific pain points.     |
| **Over-automation**           | Introducing tech debt or ignoring human insight.                           | Balance automation with manual oversight.          |
| **Ignoring culture shift**     | Teams resist change even if tools improve.                                 | Foster a **growth mindset** (e.g., demos, mentorship). |
| **Waste chasing without data** | Guessing where waste exists instead of measuring.                          | Use **value stream maps** and **process mining tools**. |
| **Kaizen fatigue**            | Too many quick changes without rest.                                       | Schedule **retreat cycles** to avoid burnout.        |

---
**Final Note**: Lean is a **mindset**, not a tool. Start small—identify **one waste type** (e.g., defects) and iterate. Track improvements transparently to build trust in the process.