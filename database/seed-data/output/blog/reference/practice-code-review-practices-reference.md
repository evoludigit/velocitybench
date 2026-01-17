# **[Pattern] Code Review Best Practices Reference Guide**
*Comprehensive documentation for structured, effective code review processes*

---

## **Overview**
Code reviews are a critical component of software quality assurance, enabling collaboration, knowledge sharing, and bug detection. This reference guide outlines **best practices** for implementing and maintaining effective code review workflows—from setup and tooling to review criteria and post-review actions. Properly structured reviews reduce technical debt, improve maintainability, and foster a culture of shared accountability.

Key principles include:
- **Consistency** – Standardized processes across teams.
- **Constructive feedback** – Focused on improvement, not blame.
- **Efficiency** – Balancing thoroughness with velocity.
- **Automation** – Leveraging tools to handle repetitive tasks.

This guide assumes familiarity with **Git-based workflows** (e.g., GitHub, GitLab, Bitbucket) and **static analysis tools** (e.g., SonarQube, ESLint).

---

## **Schema Reference**
Below is a structured breakdown of the **Code Review Best Practices Pattern**, organized by phase.

| **Category**               | **Attribute**               | **Description**                                                                                     | **Example**                                                                                     |
|----------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Setup & Tooling**        | **Review Tool**             | Platform for managing pull requests (PRs)/merge requests (MRs).                                     | GitHub, GitLab, Bitbucket, Codacy                                                               |
|                            | **Static Analysis Integration** | Tools to flag issues (code smells, vulnerabilities, syntax errors) before review.               | SonarQube, ESLint (JavaScript), Pylint (Python), Checkstyle (Java)                            |
|                            | **Review Templates**        | Structured prompts for reviewers (e.g., "Does this align with architecture decisions?").         | [GitHub Review Template Example](https://github.com/your-org/.github/blob/main/PULL_REQUEST_TEMPLATE.md) |
|                            | **Review Ownership Rules**  | Assignment logic (e.g., "Owner reviews at least one PR; peers review others").                    | "Signed-off-by" convention, mandatory secondary review for sensitive changes.                  |
| **Pre-Review Phase**       | **PR/MR Standards**         | Mandatory metadata (e.g., "Labels," "Description," "Related Issues").                           | Labels: `WIP`, `needs-design`, `breaking-change`                                              |
|                            | **Automated Checks**        | Mandatory CI/CD tests and lints before human review.                                             | `pre-commit` hooks, `PR validation checks` (e.g., "Must pass unit tests").                     |
|                            | **Change Type Classification** | Categorizing PRs (e.g., "Bug Fix," "Feature," "Refactor") for prioritization.                | GitHub Issues → Label by type                                                                 |
| **Review Process**         | **Review Criteria**         | Focus areas for reviewers (e.g., "Does this adhere to security guidelines?").                     | [SLAS Security Checklist](https://example.com/security-checklist)                             |
|                            | **Feedback Format**         | Structured feedback (e.g., "✅ Approved," "🔍 Needs clarification," "⚠️ Security concern").       | GitHub PR comments with emoji-based severity indicators                                        |
|                            | **Review Velocity Limits**  | Time thresholds (e.g., "Respond within 24 hours; resolve within 48").                            | GitHub Projects → Track review backlog                                                           |
|                            | **Escalation Paths**        | Process for unresolved conflicts (e.g., "Senior dev review if blocked >3 days").               | `@mention team lead` + `#review-escalation` label                                               |
| **Post-Review**            | **Merge Policies**          | Conditions to approve a PR (e.g., "2 approvers + CI success").                                    | GitHub: `require_code_owner_reviews=1`, `status_checks=2`                                     |
|                            | **Post-Merge Checks**       | Validation after merge (e.g., "Rollback if deployment fails").                                    | Automated alerts (e.g., Slack for failed deployments)                                         |
|                            | **Knowledge Capture**       | Documenting decisions (e.g., "Add PR to team wiki if complex").                                    | GitHub Wiki → "Key PRs of the Week"                                                              |
| **Cultural & Process**     | **Psychological Safety**    | Encouraging open dialogue (e.g., "No negative comments on personality").                         | Team guidelines: "Focus on code, not the coder"                                                |
|                            | **Ownership Rotations**     | Diversify review load (e.g., "Rotate reviewers monthly").                                         | Internal tool tracking review assignments                                                       |
|                            | **Metrics & Feedback**      | Tracking review health (e.g., "Average review time," "First-response rate").                     | GitHub Insights → "Code Review Metrics"                                                         |

---

## **Implementation Steps**
### **1. Tooling & Setup**
#### **A. Select a Review Platform**
- **GitHub/GitLab/Bitbucket**: Native PR/MR workflows with templates.
- **Dedicated Tools**: Codacy, PullReminder (for scheduling reviews).
- **Self-Hosted**: Phabricator, Gerrit (for large-scale teams).

#### **B. Configure Static Analysis**
- Integrate linters/analyzers into CI (e.g., `lint-staged` for pre-PR checks).
- Example GitHub Actions workflow:
  ```yaml
  name: Lint and Test
  on: [pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: npm install
        - run: npm run lint
        - run: npm test
  ```

#### **C. Define Review Templates**
- **GitHub Example**:
  ```markdown
  ## Before Reviewing
  - [ ] Does this align with the [Architecture Decision Records (ADRs)](link)?
  - [ ] Are there tests covering edge cases?
  - [ ] Does the PR description link to related issues?
  ```

---

### **2. Pre-Review Checklist**
| **Action**                          | **Tool/Method**                          | **Example**                                                                                     |
|-------------------------------------|------------------------------------------|-------------------------------------------------------------------------------------------------|
| Label PR by type                    | GitHub Labels                            | `type:bugfix`, `type:feat`                                                                       |
| Require CI success                  | Branch Protection Rules                 | GitHub: "Require passing tests before merging"                                                 |
| Mandate PR description              | GitHub Issue Templates                  | "Summarize changes in 3 sentences + screenshots if applicable."                                  |
| Flag "WIP" PRs                      | GitHub Draft PRs                         | `draft: true` → Blocks merges until ready                                                       |
| Enforce change size limits          | PR Size Alerts                          | Slack alert: "PR exceeds 500 lines of code"                                                     |

---

### **3. During the Review**
#### **A. Review Criteria Checklist**
| **Focus Area**          | **Questions to Ask**                                                                 | **Tools to Use**                          |
|-------------------------|-------------------------------------------------------------------------------------|-------------------------------------------|
| **Code Quality**        | Are there redundant comments? Is the code DRY?                                        | SonarQube, ESLint                         |
| **Security**            | Are passwords/logins hardcoded? Are inputs sanitized?                               | Snyk, OWASP ZAP                            |
| **Testing**             | Are edge cases covered? Are there mocks for dependencies?                            | Jest, pytest (for Python)                 |
| **Documentation**       | Are API docs updated? Are comments clear?                                            | Swagger, Doxygen                          |
| **Architecture**        | Does this comply with design patterns? Does it integrate with existing systems?     | ADRs, System Architecture Diagrams         |
| **Performance**         | Are there potential bottlenecks? Are queries optimized?                             | New Relic, DTrace (Linux)                  |

#### **B. Feedback Guidelines**
- **Do**:
  - Use **"I noticed"** or **"I think"** instead of accusations.
  - Provide **actionable suggestions** (e.g., "Consider using `map` instead of `for` loop").
  - Use **emoji shorthand** (✅/⚠️/❌) for quick visual feedback.
- **Don’t**:
  - @mention the author unless necessary.
  - Ignore repeated issues (tag as a "recurring problem").

#### **C. Common Review Patterns**
| **Pattern**               | **Use Case**                                  | **Example**                                                                                     |
|---------------------------|-----------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Line-by-Line Review**   | New devs or complex logic.                     | GitHub: "Line 42: Consider renaming `x` to `userInput` for clarity."                           |
| **Modular Review**        | Large PRs (split into files/directories).     | "Please review `src/api/` separately."                                                         |
| **Skip Review**           | Trivial fixes (e.g., typo in README).        | Label: `skip-review` + `@mention author`.                                                      |
| **Reverse Review**        | Senior devs reviewing junior dev work.         | Rotate roles to teach junior engineers.                                                        |
| **Pair Review**           | Critical PRs (e.g., security patches).        | Two reviewers + live chat (e.g., Zoom + PR comments).                                            |

---

### **4. Post-Review**
#### **A. Merge Policies**
| **Policy**                  | **GitHub Config**                     | **Example**                                                                                     |
|-----------------------------|---------------------------------------|-------------------------------------------------------------------------------------------------|
| **Approver Count**          | `require_code_owner_reviews=1`       | Require **1 code owner** + **1 peer reviewer**.                                                |
| **CI Success Required**     | Branch protection rule                | "Status checks: 2/2 required" (tests + lint).                                                  |
| **Sign-Off**                | `DCO Signed-off-by`                  | `git commit --signoff` → Enforce with Git hooks.                                                |
| **Automated Merge**         | `merge_method: squash`                | Squash commits on merge (clean history).                                                       |

#### **B. Post-Merge Actions**
- **Deploy to Staging**: Trigger a staging environment deployment.
- **Monitor Rollout**: Set up alerts for failures (e.g., Prometheus + Slack).
- **Document Decisions**: Add PR to team wiki if non-trivial (e.g., "Why we switched to React").
- **Close Related Issues**: Link PR to Jira/GitHub issues (`Fixes #123`).

---

### **5. Cultural Best Practices**
| **Principle**               | **Action Item**                                                                 | **Tool/Method**                          |
|-----------------------------|-------------------------------------------------------------------------------|-------------------------------------------|
| **Psychological Safety**    | Encourage "no blame" culture.                                                | Team agreements (e.g., "Feedback Sandbox" channel). |
| **Ownership Rotation**      | Avoid reviewer burnout.                                                       | Internal tool to track review assignments. |
| **Feedback Loops**          | Retrospectives on review pain points.                                        | Google Form → Monthly review health check. |
| **Transparency**            | Share review metrics (e.g., "Avg. review time: 12 hours").                  | GitHub Insights dashboard.                 |

---

## **Query Examples**
### **1. Finding Overdue Reviews**
**Goal**: Identify PRs waiting >48 hours for feedback.
**Query**:
```sql
-- GitHub API (GraphQL)
query {
  repository(owner: "your-org", name: "repo") {
    pullRequests(states: OPEN, first: 100) {
      nodes {
        title
        createdAt
        updatedAt
        reviews(last: 1) {
          nodes { status }
        }
      }
    }
  }
}
```
**Alternative**:
GitHub Advanced Search:
```
is:pr is:open review-requested:<your-team> -review:APPROVED -review:COMMENTED
```

### **2. Analyzing Reviewer Activity**
**Goal**: Track which reviewers are slowest.
**Query** (GitHub CLI):
```bash
gh pr list --repo your-org/repo --json reviewerLogin,reviewDecision,updatedAt --jq '[.[] | {reviewer: .reviewerLogin, status: .reviewDecision, delay: (.updatedAt | fromdate) - (.createdAt | fromdate)}] | sort_by(.delay) | reverse'
```

### **3. Counting Approvals by Author**
**Goal**: Identify top approvers.
**Query** (GitHub API):
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  "https://api.github.com/repos/your-org/repo/pulls?state=all" \
  | jq -r '.[] | .reviews[].author.*.login + ": " + (.reviews[].state == "APPROVED" | tostring)' \
  | sort | uniq -c
```

### **4. Finding PRs Without Tests**
**Goal**: Audit PRs missing test coverage.
**Query** (GitHub Search):
```
is:pr is:open "-test" "-mock" "-integration"
```

---

## **Related Patterns**
1. **[Atomic Commits Pattern]**
   - *Why it matters*: Pair with code reviews to ensure small, focused PRs.
   - *Reference*: [Atomic Commits Guide](link-to-docs).

2. **[Semi-Autonomous Teams Pattern]**
   - *Why it matters*: Encourages ownership, which aligns with review accountability.
   - *Reference*: [Semi-Autonomous Teams](link-to-docs).

3. **[Trunk-Based Development]**
   - *Why it matters*: Reduces PR complexity, making reviews faster.
   - *Reference*: [Trunk-Based Development](https://trunkbaseddevelopment.com/).

4. **[Security-First Integration]**
   - *Why it matters*: Static analysis in pre-review phase catches vulnerabilities early.
   - *Reference*: [Security in DevOps](https://www.owasp.org/index.php/DevOps).

5. **[Automated Documentation]**
   - *Why it matters*: Auto-generate docs from PR descriptions (e.g., MkDocs + GitHub Actions).
   - *Reference*: [Automated Docs with MkDocs](https://www.mkdocs.org/).

---

## **Troubleshooting**
| **Issue**                          | **Diagnosis**                          | **Solution**                                                                                     |
|-------------------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------|
| **Reviewers Ghosting**             | No comments on PRs for >72 hours.     | Set up Slack reminders: "Hey @Reviewer, any thoughts on this?"                                   |
| **PR Spam**                         | Too many trivial PRs clogging the queue. | Enforce `skip-review` for docs/non-code changes; batch small changes.                          |
| **Blocked Due to Merger Conflicts** | CI failures from diverged branches.    | Merge `main` into feature branch periodically (`git rebase`).                                    |
| **Low Approval Rate**              | PRs rejected without constructive feedback. | Mandate "Why" in feedback (e.g., "Reject because X; suggest Y.").                              |
| **Tooling Overhead**               | Static analysis slows down process.    | Prioritize critical checks (e.g., security > formatting).                                       |

---

## **Further Reading**
- [GitHub’s Code Review Guide](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews)
- [Google’s Code Review Effectiveness](https://testing.googleblog.com/2009/03/code-review-best-practices-from-google.html)
- [SonarQube’s Code Review Best Practices](https://www.sonarsource.com/resources/guide/code-review-best-practices/)
- [Microsoft’s DevOps Playbook: Code Reviews](https://docs.microsoft.com/en-us/azure/devops/project/manage-code-review-workflow)