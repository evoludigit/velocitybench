# **[Pattern] Kanban Practices Reference Guide**

---

## **1. Overview**
Kanban Practices is a lean workflow management method derived from Lean Manufacturing principles. It visualizes work as it moves through a process, limiting work-in-progress (WIP) to optimize efficiency, reduce bottlenecks, and improve flow. This guide outlines core Kanban concepts, implementation strategies, and best practices for teams adopting or refining this agile methodology.

---

## **2. Schema Reference**
The following table defines core schema elements for implementing Kanban Practices, categorized by **Concept**, **Field**, **Data Type**, **Description**, **Default Value**, and **Example**.

| **Category** | **Field**               | **Data Type**       | **Description**                                                                                                                                                                                                 | **Default** | **Example**                     |
|--------------|-------------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|----------------------------------|
| **Board**    | `board.name`            | String             | Unique name identifying the Kanban board (e.g., by project, team, or function).                                                                                                                                     | -            | "Customer Onboarding"           |
|              | `board.columns`         | Array[Column]      | Ordered list of workflow stages (e.g., "To Do," "In Progress," "Review," "Done"). Each column represents a process step.                                                                                          | -            | `[{name: "Backlog"}, ...]`      |
|              | `board.wip.limits`      | Object             | Per-column WIP limits to prevent overloading stages. Key: `column.name`, Value: `maxCount`.                                                                                                                       | -            | `{Backlog: 5, In Progress: 3}`   |
|              | `board.signals`         | Array[Signal]      | Trigger events for Kanban adjustments (e.g., "Cycle Time Violation," "Blocked Task"). See *Signal Definitions* below.                                                                                         | -            | `[{name: "Stalled Task", rule: "..."}]` |
| **Column**   | `column.name`           | String             | Stage name (e.g., "Design").                                                                                                                                                                               | -            | "Testing"                       |
|              | `column.description`    | String (Optional)  | Optional notes about the stage (e.g., "Peer review required").                                                                                                                                                  | -            | "Blocked tasks require escalation." |
| **Card**     | `card.id`               | UUID               | Unique identifier for the task/item.                                                                                                                                                                          | Auto-gen     | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6` |
|              | `card.title`            | String             | Brief, actionable description of work (e.g., "Fix login bug").                                                                                                                                                   | -            | "Add API documentation"         |
|              | `card.column`           | String             | Current workflow stage (e.g., "Development").                                                                                                                                                                    | -            | "Review"                         |
|              | `card.wip.status`       | Boolean            | True if the card is exceeding its column’s WIP limit.                                                                                                                                                               | False        | `true`                           |
|              | `card.priority`         | Enum (Low/Med/High) | Urgency level for time-sensitive tasks.                                                                                                                                                                        | Low          | "High"                           |
|              | `card.dependencies`     | Array[String]      | Linked card IDs or external tasks this card relies on.                                                                                                                                                         | -            | `["b2c3d4e5..."]`                 |
|              | `card.metrics`          | Object             | Performance data (auto-populated):                                                                                                                                                                       | -            | `{cycleTime: 48h, age: 120h}`    |
| **Signal**   | `signal.name`           | String             | Event name (e.g., "Blocked," "Stale").                                                                                                                                                                       | -            | "Cycle Time Exceeded"            |
|              | `signal.rule`           | String (YAML/JSON) | Condition to trigger the signal (e.g., `cycleTime: >72h`).                                                                                                                                                     | -            | `{card.column: "In Progress", metrics.age: >96h}` |
|              | `signal.action`         | Array[Action]      | Automated responses (e.g., notify team, pause WIP).                                                                                                                                                             | -            | `[{type: "email", recipients: "team@..."}]` |
| **Metric**   | `metric.name`           | String             | Performance indicator (e.g., "Lead Time," "Throughput").                                                                                                                                                       | -            | "Blocked Tasks"                  |
|              | `metric.type`           | Enum (Time/Count)   | Data format (e.g., hours/days vs. count).                                                                                                                                                                      | -            | "Time"                           |
|              | `metric.value`          | Number             | Current value (e.g., `3.5d` for lead time).                                                                                                                                                                       | -            | `7`                              |

---

### **Signal Definitions**
| **Signal**               | **Rule Example**                                                                 | **Default Action**                          |
|--------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| `Blocked`                | `card.column: "In Progress" && metrics.age: >24h`                             | Escalate to lead + pause WIP               |
| `Stale`                  | `card.column: "Backlog" && age: >90d`                                        | Auto-archiving after confirmation          |
| `Cycle Time Violation`   | `metrics.cycleTime: >sliding_avg + 2*std_dev`                               | Notify team + suggest review                |
| `WIP Limit Reached`      | `column.wip.limits[card.column]: > current_count`                           | Block new cards from entering column       |

---

## **3. Implementation Steps**
### **3.1 Setup**
1. **Define the Board**:
   - Create columns representing your workflow (e.g., *Backlog → Dev → Test → Done*).
   - Set WIP limits per column (e.g., 5 in *Dev*, 3 in *Test*).
   - *Tooling*: Use Trello, Jira, or custom dashboards (e.g., React + Firebase).

2. **Configure Signals**:
   - Example YAML for a "Stalled Task" signal:
     ```yaml
     signal:
       name: Stalled Task
       rule: "card.column == 'In Progress' && card.metrics.age > 48h"
       action:
         - type: email
           subject: "Task stalled for >48h"
           template: "check {{card.title}} in {{card.column}}"
           recipients: ["team@company.com", "manager@company.com"]
     ```

3. **Populate Cards**:
   - Add tasks with `title`, `priority`, and `dependencies` (if any).
   - Link cards to external systems (e.g., GitHub PRs) via `card.externalLinks`.

---

### **3.2 Core Practices**
| **Practice**            | **Description**                                                                                                                                                                                                 | **Example**                                  |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| **Visualize Work**      | Display all work in progress on a board to track bottlenecks.                                                                                                                                               | Drag-and-drop cards between *Dev/Testing*.  |
| **Limit WIP**           | Cap work-in-progress per column to reduce multitasking.                                                                                                                                                     | *Dev*: Max 5 cards; block new entries when full. |
| **Manage Flow**         | Continuously monitor cycle times, lead times, and throughput.                                                                                                                                             | Use a dashboard to alert on >72h cycle times.|
| **Explicit Policies**   | Document rules for column transitions (e.g., "Cannot move to *Test* without code review").                                                                                                                | Add `card.notes` with policy references.     |
| **Feedback Loops**      | Regularly review bottlenecks and adjust WIP limits.                                                                                                                                                         | Weekly retrospective to tweak *Test* column limits. |
| **Collaborate**         | Use comments on cards for async discussion (avoid context-switching).                                                                                                                                        | `@mention` reviewers for feedback.          |

---

### **3.3 Advanced Techniques**
- **Class-of-Service (CoS)**:
  - Categorize work into lanes (e.g., *Bug Fixes*, *New Features*) with separate WIP limits.
  - Example schema:
    ```json
    {
      "board": {
        "columns": [
          {"name": "Bug Fixes", "wip.limits": { "In Progress": 2 }},
          {"name": "New Features", "wip.limits": { "In Progress": 5 }}
        ]
      }
    }
    ```

- **Kanban for Services**:
  - Apply to non-dev workflows (e.g., customer support tickets).
  - Columns: *New → Assigned → Resolved → Closed*.

- **Automation**:
  - Trigger actions via signals (e.g., auto-label stale cards).
  - Example query to find bottlenecks:
    ```sql
    SELECT column, AVG(metrics.age)
    FROM cards
    WHERE metrics.age > 24h
    GROUP BY column
    ORDER BY AVG(metrics.age) DESC
    ```

---

## **4. Query Examples**
Use these SQL-like queries (adaptable to your tool) to analyze Kanban data.

### **4.1 Basic Queries**
| **Query**                                                                 | **Purpose**                                  |
|--------------------------------------------------------------------------|----------------------------------------------|
| `SELECT * FROM cards WHERE column = "In Progress" AND wip.status = true` | List WIP-overloaded tasks.                  |
| `SELECT column, COUNT(*) FROM cards WHERE age > 7d GROUP BY column`       | Find "stale" columns.                       |
| `SELECT title, metrics.cycleTime FROM cards ORDER BY metrics.cycleTime DESC LIMIT 5` | Top 5 longest cycle times.                  |

### **4.2 Advanced Analysis**
| **Query**                                                                 | **Purpose**                                  |
|--------------------------------------------------------------------------|----------------------------------------------|
| ```sql
SELECT
    signal.name,
    COUNT(*) AS triggers,
    AVG(card.metrics.age) AS avg_age_triggered
FROM signals
JOIN cards ON signals.card_id = cards.id
WHERE DATE(signal.timestamp) >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY signal.name
``` | Track signal frequency and average age at trigger. |
| ```sql
WITH class_of_service AS (
    SELECT
        c.title,
        c.column,
        c.priority,
        COUNT(*) OVER (PARTITION BY c.column) AS column_wip
    FROM cards c
    WHERE c.priority IN ('High', 'Critical')
)
SELECT * FROM class_of_service
WHERE column_wip >= column_wip_limits[column];
``` | Identify CoS lanes exceeding WIP.           |

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use Together**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **Scrumban**              | Hybrid of Scrum’s time-boxing and Kanban’s WIP limits.                                                                                                                                                         | Teams needing iterative planning + visual flow.   |
| **Flow Metrics**          | Focus on lead time, cycle time, and throughput.                                                                                                                                                              | Kanban teams prioritizing data-driven optimization. |
| **Swarming**              | Collaborative problem-solving on blocked tasks.                                                                                                                                                              | When signals indicate frequent bottlenecks.       |
| **Definition of Ready (DoR)** | Clarify criteria for "ready" tasks entering *In Progress*.                                                                                                                                                   | To reduce cycle time variability.                |
| **Continuous Delivery**   | Automate deployments to align with Kanban’s flow states.                                                                                                                                                            | DevOps teams using Kanban for release pipelines.   |

---

## **6. Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|-------------------------------------|----------------------------------------|-----------------------------------------------------------------------------|
| High WIP in a column                | Unclear priorities or overcommitment. | Reassess *DoR*; raise WIP limits incrementally.                            |
| Cycles stuck in *Testing*          | Blocked by dependencies or unclear requirements. | Add a *Pre-Test* column; require PR reviews before testing.              |
| Low throughput                      | Tasks too complex or poorly estimated. | Break into smaller cards; use estimation poker.                           |
| Team avoids WIP limits              | Limits are too restrictive.            | Start with conservative limits (e.g., 30% of team capacity).               |

---

## **7. Tools & Integrations**
| **Tool**               | **Features**                                                                 | **Use Case**                          |
|------------------------|------------------------------------------------------------------------------|---------------------------------------|
| Trello                 | Drag-and-drop, custom fields, power-ups (e.g., Butler for automation).      | Lightweight team boards.               |
| Jira + Kanban Plugin   | Advanced reporting, integration with DevOps tools (e.g., Bitbucket).        | Enterprise Agile teams.               |
| Miro                   | Visual workflow mapping + sticky notes for discussions.                     | Cross-functional workshops.           |
| Linear                 | Focused issue tracking with Kanban view (no "chatter" like Jira).            | Startups with minimal overhead.        |
| Custom (React + API)   | Full control over schema (e.g., add `card.tags` for categorization).       | Unique workflows (e.g., legal review). |

---
**Note**: For custom setups, extend the schema with fields like `card.tags` (e.g., `["priority/urgent", "blocked"]`) or `board.roles` (e.g., `{"owner": "Alice", "reviewer": "Bob"}`).