# **[Pattern] Post-Mortem Analysis Reference Guide**

---

## **Overview**
The **Post-Mortem Analysis** pattern is a structured approach to systematically review system failures, incidents, or critical issues to identify root causes, extract lessons learned, and prevent recurrence. This pattern ensures disciplined retrospectives in high-stakes environments such as cloud infrastructure, DevOps pipelines, or mission-critical software systems. It balances thoroughness with practicality by defining clear roles, artifacts, and actionable insights while avoiding excessive bureaucratic overhead. The goal is to foster a culture of continuous improvement by turning failures into knowledge assets for the entire team.

---

## **Schema Reference**
The following table defines the core components of a Post-Mortem Analysis. Each field is optional but recommended for comprehensive analysis.

| **Field**               | **Description**                                                                                                                                                                                                                                                                 | **Recommended Format**                                                                                     | **Example**                                                                                                         |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Incident Name**       | A unique identifier for the incident.                                                                                                                                                                                                                                   | Alphanumeric, descriptive (e.g., `PM-2023-04-12`).                                                       | `PM-20230412-S3BucketCorruption`                                                                                 |
| **Incident Type**       | Classification of the incident (e.g., failure, outage, security breach, performance degradation).                                                                                                                                                               | Enumerated list (predefined taxonomy).                                                                       | `Production Outage`                                                                                              |
| **Incident Date/Time**  | Start and end timestamps of the incident (UTC).                                                                                                                                                                                                                     | ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`).                                                                   | `2023-04-12T14:30:00Z – 2023-04-12T16:15:00Z`                                                                  |
| **Affected Systems**    | List of systems, services, or components impacted.                                                                                                                                                                                                               | Bulleted list, tags, or links to runbooks.                                                                   | - AWS ECS Cluster<br>- Redis Cache (primary)<br>- Logging Service (partially)                                  |
| **Impact**              | Quantitative/qualitative measure of the incident’s effect (e.g., downtime minutes, revenue loss, user impact).                                                                                                                                          | Numeric + narrative (e.g., "90 min SLO violation; $12K revenue loss").                                      | `90 minutes SLO violation; 5% uptime SLA breach; 1,200 users affected`                                            |
| **Root Cause**          | Primary cause of the incident (e.g., misconfiguration, race condition, third-party failure).                                                                                                                                                                    | Concise statement (1-3 sentences).                                                                         | `Misconfigured IAM policy allowed S3 bucket deletion by ECS task; lack of multi-factor authentication.`          |
| **Contributing Factors**| Secondary causes or exacerbating conditions (e.g., poorly documented workflows, alert fatigue).                                                                                                                                                              | Bullet points or diagram (fishbone/cause-and-effect).                                                      | - No pre-incident failure drill for IAM reviews<br>- Alert suppression rules ignored during peak traffic    |
| **Short-Term Mitigations** | Immediate fixes implemented to resolve the incident.                                                                                                                                                                                                              | Checklist or timeline.                                                                            | 1. Reverted IAM policy via CloudTrail review<br>2. Rolled back ECS tasks<br>3. Alerted on SARS metrics    |
| **Long-Term Fixes**      | Permanent solutions or process improvements.                                                                                                                                                                                                                 | SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound).                                       | **"Enforce IAM least privilege via policy-as-code with CI/CD gate; complete by Q3 2023."**                     |
| **Metrics for Success** | KPIs to validate the effectiveness of fixes (e.g., "Reduce S3 policy drift by 80%").                                                                                                                                                                     | SMART metrics.                                                                                               | `"Zero unapproved IAM changes in production by Q4 2023 (tracked via GitOps audits)."`                          |
| **Action Items**        | Owners, deadlines, and status for each improvement task.                                                                                                                                                                                                             | Table with columns: Owner, Deadline, Status, Priority.                                                      | | **Owner**       | **Deadline**   | **Status** | **Priority** |<br>| Alice Zhang | Jun 30, 2023 | ✅ Completed | High     |<br>| DevOps Team | Sep 30, 2023 | ⏳ In Progress | Medium   |
| **Lessons Learned**     | Generalizable insights for the team (e.g., "Automate IAM drift detection").                                                                                                                                                                             | Thematic categories (e.g., "Process," "Technology," "Culture").                                              | - **"Process": Schedule quarterly IAM access reviews.**<br>- **"Technology": Integrate S3 versioning + MFA.**   |
| **Documentation Updates**| References to updated runbooks, diagrams, or knowledge bases.                                                                                                                                                                                              | Links to wiki pages, Confluence docs, or Git repos.                                                          | [AWS IAM Policy Review Checklist (v3)](https://company.wiki/iam-checklist)                                         |
| **Participants**        | Roles involved (e.g., engineers, SREs, PMs, security).                                                                                                                                                                                                           | List with optional email/Slack handles.                                                                     | - **Engineering Lead**: Bob Smith<br>- **SRE**: Charlie Lee (@charleelee)<br>- **Security**: Dana Kim         |
| **Status**              | Current stage of analysis (e.g., "Draft," "Approved," "Closed").                                                                                                                                                                                       | Enumerated list.                                                                                             | `Approved (Priority: High)`                                                                                     |
| **Attachments**         | Supporting artifacts (e.g., logs, screenshots, diagrams).                                                                                                                                                                                                  | Links or embedded (e.g., GitHub Gist, S3 object URLs).                                                      | [ECS Task Logs](s3://company-logs/ecs/2023-04-12/)<br>[Root Cause Diagram](https://miro.com/app/board...)      |

---

## **Query Examples**
### **1. Searching for Incidents by Root Cause**
**Use Case**: Identify all post-mortems related to "misconfigured IAM."
**Query (SQL-like pseudocode for a database):**
```sql
SELECT incident_name, incident_date, root_cause, contributing_factors
FROM post_mortems
WHERE LOWER(root_cause) LIKE '%iam%'
   OR LOWER(contributing_factors) LIKE '%iam%';
```
**API Example (REST):**
```http
GET /api/v1/post-mortems
  ?filter=root_cause:iam
  &sort=incident_date:desc
  &limit=10
```

### **2. Filtering Open Action Items**
**Use Case**: Find all unresolved post-mortems with "High" priority.
**Query:**
```sql
SELECT incident_name, action_items.owner, action_items.deadline, action_items.status
FROM post_mortems
JOIN action_items ON post_mortems.incident_name = action_items.incident_name
WHERE action_items.status = '⏳ In Progress'
  AND action_items.priority = 'High';
```

### **3. Generating a Dashboard of Recurring Themes**
**Use Case**: Visualize common root causes over time.
**Query:**
```sql
SELECT root_cause, COUNT(*) as frequency
FROM post_mortems
GROUP BY root_cause
ORDER BY frequency DESC;
```
**Tools**:
- **Dashboards**: Grafana, Tableau (with a PostgreSQL backend).
- **Automation**: Python script to generate Markdown summaries:
  ```python
  import pandas as pd
  df = pd.read_csv("post_mortems.csv")
  themes = df["root_cause"].value_counts().to_markdown()
  with open("themes.md", "w") as f:
      f.write(themes)
  ```

---

## **Implementation Guidelines**
### **1. Roles and Responsibilities**
| **Role**               | **Responsibilities**                                                                                                                                                                                                                     |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Scribe**             | Documents the post-mortem (neutral, objective voice). Attends incident calls and synthesizes input.                                                                                                                         |
| **Technical Leads**     | Provides deep dives on root causes; validates fixes.                                                                                                                                                                       |
| **Product Manager**     | Aligns findings with business goals; prioritizes action items.                                                                                                                                                              |
| **Security Team**       | Reviews for vulnerabilities (e.g., misconfigurations, privilege escalation paths).                                                                                                                                          |
| **Participants**        | All engineers, SREs, and stakeholders involved in the incident. *Note*: Avoid "blame culture"—focus on systemic improvements.                                                                                        |

### **2. Structure the Post-Mortem**
Follow this **template** for consistency:
1. **Incident Recap**: Timeline with key events (use a timeline diagram).
   - *Example*:
     ```
     14:30 UTC: ECS task fails with "AccessDenied" (S3).
     14:45 UTC: Manual S3 bucket deletion detected (CloudTrail).
     14:55 UTC: Rollback initiated.
     ```
2. **Root Cause**: Use the **"5 Whys"** technique to drill down.
   - *Example*:
     - **Why** did the ECS task fail? → *Missing IAM permission.*
     - **Why** was the permission missing? → *IAM policy updated but not reviewed.*
3. **Lessons Learned**: Categorize into:
   - **Technology**: Tools/processes to improve (e.g., "Add S3 MFA delete").
   - **Process**: Workflows (e.g., "Require 2 engineers for IAM changes").
   - **Culture**: Mindset shifts (e.g., "Normalize speaking up about risks").

### **3. Best Practices**
- **Timebox**: Limit post-mortems to **2 hours max** for retrospectives; **1 week** for documentation.
- **Automate Data Collection**:
  - Pull logs from tools like **Datadog**, **AWS CloudTrail**, or **Prometheus**.
  - Use **Incident Management Platforms** (e.g., PagerDuty, Opsgenie) to auto-gather artifacts.
- **Link to Runbooks**: Update runbooks with post-mortem insights (e.g., "S3 Bucket Recovery").
- **Share Widely**:
  - Publish anonymized versions for the broader team (redact sensitive data).
  - Use **internal wikis** (Confluence) or **newsletters** (e.g., monthly "Lessons Learned" digest).
- **Follow Up**: Track action items in a **Kanban board** (Jira, Linear) with deadlines.

### **4. Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Why It’s Bad**                                                                                                                                                                                                                     | **Fix**                                                                                                      |
|---------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Lack of Ownership**           | No clear owner for action items leads to stagnation.                                                                                                                                                                       | Assign owners with deadlines; use tools like Jira to track progress.                                      |
| **Overly Blame-Focused**        | Shaming individuals discourages transparency.                                                                                                                                                                             | Frame discussions as **"system failures"** not personal mistakes.                                         |
| **No Metrics for Success**      | Improvements without KPIs may not be measured.                                                                                                                                                                             | Define **SMART metrics** (e.g., "Reduce incident MTTR by 30%").                                             |
| **Documentation Sooner**        | Writing while incident is fresh ensures accuracy.                                                                                                                                                                           | Start drafting during the call; finalize within 48 hours.                                                   |
| **Ignoring Contributing Factors** | Only addressing root causes leaves gaps.                                                                                                                                                                               | Include **secondary causes** (e.g., alert fatigue, poor documentation).                                     |

---

## **Query Examples: Advanced**
### **1. Time-to-Resolution Analysis**
**Goal**: Identify trends in incident recovery times.
**Query**:
```sql
SELECT
    incident_type,
    AVG(TIMESTAMPDIFF(minute, incident_date, resolution_date)) as avg_minutes,
    COUNT(*) as incidents
FROM post_mortems
WHERE resolution_date IS NOT NULL
GROUP BY incident_type
ORDER BY avg_minutes DESC;
```
**Visualization**: Bar chart in Grafana with incident types on the x-axis.

### **2. Owner Performance**
**Goal**: Track which teams/individuals have unresolved action items.
**Query**:
```sql
SELECT
    owner_role,
    COUNT(*) as unresolved_items,
    SUM(CASE WHEN deadline < CURRENT_DATE THEN 1 ELSE 0 END) as overdue
FROM action_items
WHERE status = '⏳ In Progress'
GROUP BY owner_role
ORDER BY overdue DESC;
```

### **3. Root Cause Trend Analysis**
**Goal**: Flag recurring themes (e.g., "Database connection leaks").
**Query**:
```sql
WITH root_cause_frequencies AS (
    SELECT
        root_cause,
        COUNT(*) as frequency,
        ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank
    FROM post_mortems
    GROUP BY root_cause
)
SELECT rc.root_cause, rc.frequency, rc.rank
FROM root_cause_frequencies rc
WHERE rc.rank <= 3; -- Top 3 causes
```

---

## **Related Patterns**
1. **[Runbook Automation](https://example.com/runbook-pattern)**
   - *Synergy*: Post-mortems often identify gaps that can be automated in runbooks (e.g., "Add a playbook for S3 bucket recovery").
   - *Use Case*: Document remedial steps during the post-mortem, then automate them.

2. **[Incident Response Playbook](https://example.com/incident-playbook)**
   - *Synergy*: Post-mortems rely on playbooks for timeline reconstruction; playbooks should reference post-mortem insights.
   - *Use Case*: Update playbooks with lessons from "failed command-line operations."

3. **[Blameless Post-Mortems](https://example.com/blameless-postmortems)**
   - *Synergy*: The Post-Mortem pattern often borrows from blameless practices (e.g., focusing on systems, not people).
   - *Use Case*: Use frameworks like **Google’s "How Google Does Postmortems"** to structure discussions.

4. **[Technical Debt Tracking](https://example.com/technical-debt)**
   - *Synergy*: Long-term fixes from post-mortems often relate to technical debt (e.g., "Refactor logging service").
   - *Use Case*: Tag action items as "Technical Debt" in your project tracker.

5. **[Chaos Engineering](https://example.com/chaos-engineering)**
   - *Synergy*: Post-mortems help identify "Chaos Experiment" opportunities (e.g., "Test S3 bucket deletion under load").
   - *Use Case*: Use findings to design **Controlled Chaos** scenarios.

---
## **Tools and Templates**
| **Category**            | **Tools/Resources**                                                                                                                                                                                                       | **Link**                                                                                                   |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Post-Mortem Software** | Tools for structured post-mortems with collaboration.                                                                                                                                                                   | [Incident.io](https://www.incident.io/), [Blameless](https://www.blameless.com/)                          |
| **Wikis**               | Centralize post-mortem documentation.                                                                                                                                                                                 | [Confluence](https://www.atlassian.com/software/confluence), [Notion](https://www.notion.so/)             |
| **Diagramming**         | Visualize root causes (e.g., fishbone diagrams).                                                                                                                                                                   | [Miro](https://miro.com/), [Lucidchart](https://www.lucidchart.com/)                                      |
| **Logging/Observability** | Correlate post-mortem findings with real-time data.                                                                                                                                                                 | [Datadog](https://www.datadoghq.com/), [Grafana](https://grafana.com/)                                    |
| **Templates**           | Ready-made post-mortem frameworks.                                                                                                                                                                                  | [GitHub Post-Mortem Template](https://github.com/your-org/postmortem-template), [Netflix Post-Mortem Guide](https://netflix.github.io/general/2015/02/21/designing-for-failure.html) |

---
## **Further Reading**
1. **"Site Reliability Engineering" (Google SRE Book)** – Chapter 9: Postmortems.
   - *Key Takeaway*: Why post-mortems are critical for SLO/SLI alignment.
2. **Blameless Postmortems (Chaos Engineering)** – [Gergely Orosz’s Blog](https://www.oryx-analytics.com/blog/postmortem-cultures).
   - *Key Takeaway*: How to balance accountability with psychological safety.
3. **AWS Well-Architected Post-Mortem Framework** – [AWS Whitepaper](https://aws.amazon.com/architecture/well-architected/postmortem-framework/).
   - *Key Takeaway*: Cloud-specific patterns for IAM, networking, and storage incidents.