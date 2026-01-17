# **[Pattern] Agile Scrum Practices – Reference Guide**

---

## **1. Overview**
The **Agile Scrum Practices** pattern describes a lightweight, iterative framework for delivering complex projects efficiently. Scrum defines three key roles (**Product Owner**, **Scrum Master**, and **Development Team**), as well as time-boxed events (**Sprints**, **Daily Stand-ups**, **Sprint Review**, **Retrospective**, and **Planning**) to foster adaptability, transparency, and continuous improvement. This guide provides a structured reference for implementing Scrum practices, including roles, ceremonies, artifacts, and best practices.

---

## **2. Schema Reference**

Scrum is structured around three **roles**, five **events**, and three **artifacts**:

| **Category**  | **Component**               | **Description**                                                                                     | **Key Responsibilities/Outputs**                                                                                     |
|----------------|----------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **Roles**      | **Product Owner**           | Represents stakeholders; maximizes product value.                                                   | Defines Product Backlog, prioritizes features, ensures clarity, accepts/rejects work increments.                     |
|                | **Scrum Master**            | Facilitates Scrum processes; removes impediments.                                                    | Coaches the team, shields from distractions, ensures adherence to Scrum theory, resolves conflicts.                   |
|                | **Development Team**        | Cross-functional group that delivers work each Sprint.                                               | Self-organizing; commits to Sprint Goals, estimates effort, delivers "Done" increments.                            |
| **Events**     | **Sprint** (1–4 weeks)       | Time-boxed iteration where a "Done" product increment is created.                                    | Team plans (Sprint Planning), executes work, and delivers results.                                               |
|                | **Sprint Planning**         | Time-boxed (≤8h) event to define Sprint Goals and select Backlog items.                               | Team commits to a Sprint Backlog, identifies risks, and sets realistic targets.                                  |
|                | **Daily Stand-up**          | 15-minute time-boxed sync to synchronize progress.                                                     | Team answers: *What did I do? What will I do? Any blockers?* (No deep discussion—blockers escalated to SM).       |
|                | **Sprint Review**           | 4-hour time-boxed demo of work completed.                                                            | Team demonstrates increments to stakeholders; feedback informs future Sprints.                                  |
|                | **Sprint Retrospective**    | 3-hour time-boxed reflection on process improvements.                                                 | Team identifies strengths, challenges, and actionable improvements for the next Sprint.                            |
| **Artifacts**  | **Product Backlog**         | Ordered list of features, bugs, and improvements.                                                    | Continuously refined; prioritized by the Product Owner.                                                         |
|                | **Sprint Backlog**          | Subset of the Product Backlog selected for the Sprint.                                               | Team-owned; refined during Sprint Planning; tracks progress via Sprint Burndown Chart.                            |
|                | **Increment**                | Sum of all "Done" work from completed Sprints.                                                       | Must be usable, though not necessarily shippable, per Definition of "Done."                                       |

---
**Key Principle:** *Scrum is empirical—transparency (artifacts), inspection (events), and adaptation (retrospectives) drive continuous improvement.*

---

## **3. Query Examples**

### **3.1. Sprint Planning**
**Scenario:** *How do we select Backlog items for the next Sprint?*

1. **Input:** Current Product Backlog (prioritized by the PO).
2. **Action:**
   - Team reviews top items and estimates effort (e.g., Story Points).
   - Discusses dependencies and risks.
3. **Output:** Sprint Backlog with selected items, committed velocity, and Sprint Goal.
4. **Tools:** Kanban board (e.g., Jira, Trello), planning poker (for estimation).

**Template:**
```
Sprint Planning Checklist:
✅ Backlog items ready? (Clear, defined, estimated)
✅ Team available for full Sprint duration?
✅ Sprint Goal agreed upon?
✅ Risks identified and mitigated?
```

---

### **3.2. Daily Stand-up**
**Scenario:** *How do we run an effective Daily Stand-up?*

1. **Format:** *Standing meeting* (3 questions per team member):
   - *What did I do yesterday?*
   - *What will I do today?*
   - *Are there any blockers?*
2. **Time-box:** 15 minutes max.
3. **Output:** Action items logged (e.g., in a shared doc or ticketing system).
4. **Anti-patterns:**
   - No deep discussions (save for after the meeting).
   - Blockers must be addressed by the Scrum Master before the next Stand-up.

**Example Output:**
| Team Member | Yesterday’s Work | Today’s Work | Blockers |
|-------------|------------------|--------------|----------|
| Alice       | Fixed API bug    | Test new feature | None     |
| Bob         | -                | Refactor code | Needs DB access |

---

### **3.3. Sprint Review**
**Scenario:** *How do we demonstrate work to stakeholders?*

1. **Prep:**
   - Team prepares a demo of completed increments (not just "Done" tickets).
   - Identify stakeholders (e.g., business, QA, UX).
2. **Agenda:**
   - Demo (15–30 min).
   - Stakeholder feedback (15–30 min).
   - Planning for next Sprint (15 min).
3. **Tools:** Demo environment, shared screen, feedback form.

**Prompt for Stakeholders:**
*"What did you learn today? What should we change next Sprint?"*

---
### **3.4. Sprint Retrospective**
**Scenario:** *How do we identify process improvements?*

1. **Format:** Structured discussion (not a status meeting).
   - *What went well?* (Strengths)
   - *What could improve?* (Challenges)
   - *Actionable items* (SM tracks follow-up)
2. **Time-box:** 3 hours max.
3. **Technique:** *Start-Stop-Continue* or *Mad/Sad/Glad* for quick input.
4. **Output:** Action items assigned to team members.

**Example Action Items:**
- [ ] Reduce context-switching by batching tasks.
- [ ] SM to facilitate better estimation workshops.
- [ ] Team to refine Backlog items before Sprint Planning.

---
### **3.5. Product Backlog Refinement**
**Scenario:** *How do we keep the Backlog healthy?*

1. **Frequency:** Ongoing (e.g., 1–2 hours/week).
2. **Participants:** PO + Development Team.
3. **Actions:**
   - Clarify ambiguous stories.
   - Update estimates.
   - Split large items (INVEST principle: *Independent, Negotiable, Valuable, Estimable, Small, Testable*).
4. **Tools:** Backlog grooming sessions (Jira, Trello).

**Rule of Thumb:**
*"If an item isn’t ready for a Sprint, it doesn’t belong in the Sprint Backlog."*

---

## **4. Implementation Best Practices**

### **4.1. Roles**
- **Product Owner:**
  - Spend 100% of time on the product (if possible).
  - Regularly collaborate with the team to refine Backlog items.
- **Scrum Master:**
  - Focus on *serving the team*, not managing them.
  - Remove impediments (track in a "Blockers" board).
- **Development Team:**
  - Be self-organizing (no micromanagement).
  - Define "Done" (e.g., code reviewed, tested, documented).

### **4.2. Events**
- **Time-boxing:** Strict adherence to durations (e.g., Sprint Review ≤4h).
- **Accountability:** If an event is missed, it must be replanned (not skipped).
- **Transparency:** All artifacts must be visible (e.g., Burndown Chart in public).

### **4.3. Artifacts**
- **Product Backlog:**
  - Never static—continuously refined.
  - Use acceptance criteria (e.g., *As a [user], I want [feature] so that [benefit]*).
- **Sprint Backlog:**
  - Updated daily (e.g., via Kanban columns: *To Do | In Progress | Done*).
- **Increment:**
  - Must meet the Definition of "Done" (e.g., tested, deployed to staging).

### **4.4. Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Why It’s Bad**                          | **Fix**                                  |
|---------------------------------|-------------------------------------------|------------------------------------------|
| "Scrum-but" (e.g., longer Sprints) | Loses agility; burnout risk.              | Stick to 1–4 week Sprints.               |
| No Retrospective               | No opportunity for improvement.           | Mandate retrospectives every Sprint.      |
| PO dictates Sprint Backlog      | team loses ownership.                     | Collaborative planning.                  |
| No Definition of "Done"         | Increment not truly usable.               | Team agrees on "Done" criteria upfront.  |

---

## **5. Related Patterns**

| **Pattern**                     | **How It Complements Scrum**                                                                 | **When to Use Together**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Kanban**                       | Provides visual flow for continuous work (vs. Scrum’s time-boxed Sprints).                  | Use Kanban for support/operations; Scrum for new product development.                  |
| **Lean Startup**                 | Encourages rapid experimentation and pivoting, aligning with Scrum’s iterative approach.     | Pair with Scrum to validate assumptions early.                                         |
| **DevOps**                       | Automates testing/deployment, enabling "Done" increments to be delivered frequently.        | Critical for Scrum teams shipping software increments.                                 |
| **User Story Mapping**           | Helps PO and team visualize flow and prioritize Backlog items.                               | Use before Sprint Planning to clarify scope.                                          |
| **Technical Debt Tracking**      | Monitors quality risks that can derail Sprints.                                            | Pair with Scrum’s Retrospectives to address technical debt proactively.                 |
| **SAFe (Scaled Agile Framework)**| Provides Scrum scaling for large organizations (e.g., multiple teams).                     | Use when Scrum teams need to coordinate at scale.                                     |

---
## **6. Troubleshooting Common Issues**

| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|------------------------------------|----------------------------------------|------------------------------------------------------------------------------|
| Team misses Sprint Goal            | Unrealistic estimates or scope creep.  | Re-estimate remaining work; adjust future capacity.                         |
| Low team morale                    | Too many blockers or interruptions.    | Scrum Master investigates root causes; protect team from distractions.       |
| Stakeholders unhappy with review   | Unclear expectations or incomplete work.| PO ensures Backlog items are well-defined; team demonstrates usable increments. |
| Retrospectives feel pointless       | No action items or follow-up.          | SM tracks action items; celebrate progress in retrospectives.               |

---
## **7. Tools & Resources**
| **Category**       | **Tools**                                                                 | **Key Features**                                                                 |
|--------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Project Management** | Jira, Azure DevOps, Trello                                         | Backlog management, Burndown Charts, Sprint tracking.                          |
| **Communication**  | Slack, Microsoft Teams, Jira Chat                                    | Real-time collaboration for Daily Stand-ups and blockers.                      |
| **Estimation**     | Planning Poker (Physical/Digital), Toggl Plan                         | Engages team in collaborative estimation.                                     |
| **Retrospectives** | Miro, Lucidchart, Retrium                                            | Visual boards for structured retrospective exercises.                          |
| **Continuous Integration** | Jenkins, GitHub Actions, CircleCI                                    | Automates testing/deployment for "Done" increments.                           |

---
**Final Note:** Scrum is a *framework*, not a process. Adopt its principles while tailoring events/roles to your context. Start small—pilot Scrum with one team before scaling.