# **[Pattern] Reference Guide: Breaking Changes**

---

## **Overview**
The **Breaking Changes** pattern is a structured approach to documenting deliberate API, library, or software version updates that may render existing code incompatible. This ensures developers are **prepared, warned, and supported** during upgrades, minimizing disruption while maintaining transparency. Breaking changes should be documented clearly with **impact assessments, migration strategies, and affected versions** to enable smooth adoption.

This guide explains how to **identify, describe, and manage** breaking changes to reduce friction in production environments.

---

## **Implementation Details**

### **Key Concepts**
| **Concept**               | **Description**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|
| **Breaking Change**       | A deliberate modification that alters backward compatibility (e.g., renaming fields, removing features, or changing behaviors). |
| **Impact Assessment**     | A documented evaluation of affected components, data, and dependencies.       |
| **Version Scope**         | The release(s) where the change is introduced/deprecated (e.g., `v3.0.0`).     |
| **Migration Strategy**    | Steps to update code, configurations, or workflows to handle the change.       |
| **Notice Period**         | Timeframe (e.g., 6 months) between announcement and enforcement.                |
| **Rollback Plan**         | Procedures to revert to a stable version if issues arise.                      |

---

## **Schema Reference**
Below is a structured **Breaking Change (BC) document schema** that standardizes format and ensures completeness.

| **Field**               | **Type**       | **Description**                                                                 | **Example**                                                                 |
|-------------------------|----------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `id`                    | `string`       | Unique identifier for the breaking change (e.g., `BC-2024-001`).                | `BC-2024-001`                                                               |
| `versionIntroduced`     | `string`       | Version where the change is introduced (semantic versioning).                   | `v3.2.0`                                                                     |
| `versionDeprecated`     | `string`       | Version where the old behavior is no longer supported.                          | `v3.1.0` (deprecated in this version)                                        |
| `versionRemoved`        | `string`       | Version where the deprecated feature is fully removed (if applicable).          | `v4.0.0` (removed in this version)                                           |
| `severity`              | `enum`         | Criticality level (`low`, `medium`, `high`).                                    | `high`                                                                       |
| `affectedComponents`    | `array`        | List of modules, APIs, or configurations impacted.                               | `["auth-service", "data-model"]`                                            |
| `affectedData`          | `array`        | Data structures, schemas, or formats changed.                                   | `["UserProfileSchema"]`                                                     |
| `description`           | `string`       | Clear explanation of the change and its purpose.                                | `"The `loginToken` field in `UserProfileSchema` is now required."`         |
| `impact`                | `string`       | Consequences if not migrated (e.g., runtime errors, data corruption).          | `"Old tokens will fail authentication."`                                    |
| `migrationSteps`        | `array`        | Step-by-step guide to update code/configurations.                               | `[{step: "1. Add `loginToken` to UserProfile inputs.", code: "..."}]`     |
| `rollbackPlan`          | `array`        | Steps to revert to the previous stable version.                                | `[{step: "Downgrade to v3.1.0 and restart service.", link: "/rollback-guide"}]` |
| `noticePeriod`          | `date`         | Date by which users must migrate (if enforced).                                | `"2024-06-30"`                                                              |
| `references`            | `array`        | Links to PRs, release notes, or related docs.                                   | `[{url: "/release-notes/v3.2.0", type: "release"}]`                         |
| `openIssues`            | `array`        | Tracking bugs or edge cases related to the change.                              | `[{id: "ISSUE-123", status: "open"}]`                                       |

---
**Example BC Document (JSON-like):**
```json
{
  "id": "BC-2024-001",
  "versionIntroduced": "v3.2.0",
  "versionDeprecated": "v3.1.0",
  "severity": "high",
  "affectedComponents": ["auth-service"],
  "affectedData": ["UserProfileSchema"],
  "description": "The `loginToken` field is now required in API requests.",
  "impact": "Unauthenticated requests will fail.",
  "migrationSteps": [
    {
      "step": "1. Update API calls to include `loginToken`.",
      "code": "fetch('/api/user', { headers: { Authorization: `Bearer ${token}` } })"
    }
  ],
  "rollbackPlan": [
    { "step": "Downgrade to v3.1.0.", "link": "/rollback" }
  ],
  "noticePeriod": "2024-06-30",
  "references": [
    { "url": "/release-notes/v3.2.0", "type": "release" }
  ]
}
```

---

## **Query Examples**
### **1. Filtering BCs by Version**
Retrieve all breaking changes introduced in `v3.0.0` or later:
```graphql
query BreakingChangesByVersion($minVersion: String!) {
  breakingChanges(
    filter: { versionIntroduced: { gte: $minVersion } }
  ) {
    id
    versionIntroduced
    description
    severity
  }
}
```
**Input Variable:**
```json
{ "minVersion": "v3.0.0" }
```
**Output:**
```json
{
  "data": {
    "breakingChanges": [
      { "id": "BC-2024-001", "versionIntroduced": "v3.2.0", ... },
      { "id": "BC-2024-002", "versionIntroduced": "v3.1.0", ... }
    ]
  }
}
```

---

### **2. Searching for BCs by Component**
Find breaking changes affecting the `data-model`:
```sql
SELECT * FROM breaking_changes
WHERE 'data-model' IN affected_components
ORDER BY version_introduced DESC;
```
**Result Table:**
| `id`    | `versionIntroduced` | `description`                          |
|---------|---------------------|----------------------------------------|
| BC-2024-003 | v3.3.0               | `UserProfileSchema` fields renamed.    |
| BC-2024-004 | v3.0.0               | `PostgreSQL` connection timeout changed. |

---

### **3. API Client Migration Check**
Generate a checklist for upgrading from `v2.x` to `v3.2.0`:
```bash
#!/bin/bash
# Script to fetch BCs between versions, filtered for critical issues.
curl -X POST "https://api.example.com/breaking-changes" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "versionIntroduced": { "gte": "v3.2.0" },
      "versionDeprecated": { "lte": "v2.9.9" },
      "severity": "high"
    }
  }'
```
**Output (human-readable):**
```
⚠️  Critical Breaking Changes Detected (v3.2.0):
  1. BC-2024-001: `loginToken` is now required in auth-service.
     Migration: Update API calls to include token.
  2. BC-2024-005: `legacyAuth` deprecated.
     Migration: Migrate to JWT-based authentication.
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                                  |
|---------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **[Semantic Versioning](https://semver.org/)** | Standard for versioning to signal breaking changes via `MAJOR` increments.   | Clarifying backward compatibility.           |
| **[Feature Flags](https://martinfowler.com/bliki/FeatureToggle.html)** | Gradual rollout of breaking changes behind flags.                          | Minimizing risk during transitions.          |
| **[Deprecation Policy](https://github.com/tc39/proposal-deprecation)** | Clear communication of deprecated APIs before removal.                     | Phased adoption (e.g., JavaScript `fetch`).  |
| **[Backward-Compatible API Design](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ch08.html)** | Strategies to reduce breaking changes (e.g., additive APIs).              | Long-term API stability.                     |
| **[Change Data Capture (CDC)](https://www.cockroachlabs.com/docs/stable/learn/transactions.html)** | Sync breaking changes to databases without downtime.                     | Database schema migrations.                  |

---

## **Best Practices**
1. **Notify Early**: Publish breaking changes **6–12 months** before enforcement (use release notes or email alerts).
2. **Prioritize**: Flag `high`-severity changes with urgency (e.g., security patches).
3. **Provide Examples**: Include **code snippets** and **integration tests** for migrations.
4. **Test Rollbacks**: Validate rollback procedures in staging.
5. **Document Workarounds**: Temporary solutions (e.g., feature flags) until migration completes.
6. **Avoid Surprises**: Align breaking changes with **major version bumps** (semantic versioning).

---
## **Example Workflow**
1. **Developer Requests a Change**: A team proposes removing the `legacyAuth` endpoint.
2. **Impact Assessment**: Docs the `high`-severity BC, lists affected APIs, and drafts migration steps.
3. **Review**: Technical writers validate clarity; stakeholders approve timeline.
4. **Announcement**: Publishes BC doc in `v3.1.0` with a **6-month notice period**.
5. **Migration Support**: Provides a **migration helper library** and **training sessions**.
6. **Enforcement**: Deprecation removed in `v4.0.0`; old endpoints return `403 Forbidden`.

---
## **Tools to Implement**
| **Tool**               | **Purpose**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **GitHub/GitLab Labels** | Tag breaking changes (e.g., `breaking-change`).                             |
| **Confluence/Jira**     | Centralized BC documentation with version tracking.                        |
| **Semantic Release**    | Automate BC notices in changelogs (GitHub Actions).                         |
| **Postman/Newman**      | Test APIs against breaking changes pre-migration.                          |
| **Sentry/Error Tracking** | Monitor migration failures post-deployment.                                |

---
## **Troubleshooting**
| **Issue**               | **Solution**                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| **Users ignore notices** | Enforce **pre-release checks** (e.g., CI blocks `v4.0.0` if `legacyAuth` is used). |
| **Incomplete migration** | Provide a **downgrade script** or **feature toggle** until adoption.         |
| **Data corruption**      | Offer a **schema migration tool** (e.g., Flyway, Alembic).                  |
| **Legacy codebase**      | Create a **compatibility layer** (e.g., `@deprecated` decorator in TypeScript). |

---
## **Further Reading**
- [Semantic Versioning 2.0.0](https://semver.org/)
- [Google’s Deprecation Policy](https://developers.google.com/velocity/schedules/deprecation)
- [Breaking Changes for APIs (Kin Lane)](https://apievangelist.com/2019/01/17/how-to-write-apis-that-dont-break/)
- [Postman’s API Breaking Change Guide](https://learning.postman.com/docs/designing-and-developing-your-api/versioning-your-api/)

---
**Last Updated:** [Insert Date]
**Maintainers:** [Team Names]