# **[Pattern] Consistency Best Practices – Reference Guide**

## **Overview**
This reference guide outlines **Consistency Best Practices**, a design pattern aimed at ensuring uniform behavior, terminology, and structure across systems, platforms, or user interactions. Inconsistencies in UI, data handling, or workflows lead to cognitive friction, reduced usability, and technical debt. This pattern provides principles, guidance, and enforceable practices to maintain cohesion in:
- **User Interface (UI) and Experience (UX):** Layout, terminology, navigation, and accessibility
- **Data Models and APIs:** Schema design, field naming, response formats
- **System Behavior:** Error handling, edge-case management, and transactional logic
- **Code and Architecture:** Naming conventions, error handling, and logging

By applying these best practices, teams can reduce bugs, improve maintainability, and deliver a seamless experience for both users and developers.

---

## **Schema Reference**
Below is a structured breakdown of key **Consistency Best Practices** categories, their sub-practices, and implementation rules.

| **Category**               | **Sub-Practice**                          | **Implementation Rule**                                                                                     | **Example**                                                                                     |
|----------------------------|-------------------------------------------|--------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **UI/UX Consistency**      | Terminology                             | Use standardized terms across all screens, tooltips, and helping text.                                     | ← Back → vs. ← Previous Page → → Use "Cancel" instead of "Exit" everywhere.                     |
|                            | Visual Hierarchy                        | Align typography, color coding (e.g., primary/secondary buttons), and spacing rules across components.      | Primary buttons: `#0066cc` background, 16px padding; Secondary: `#ccc` background, 12px padding.    |
|                            | Navigation                             | Ensure consistent location and labeling of navigation elements (menus, breadcrumbs, CTA buttons).         | All dashboards share "Settings" in the top-right corner.                                        |
|                            | Error States                            | Uniform error message formats (e.g., `{errorCode}: {description}`) and visual cues (e.g., red borders).     | Error: `400: Invalid Input – "Email" must be 10+ characters.`                                     |
| **Data/API Consistency**   | Schema Naming                          | Use consistent field names (e.g., `snake_case` for internal APIs, `camelCase` for frontend).               | `{ userId: 123 }` (frontend) ↔ `{ user_id: 123 }` (database).                                 |
|                            | Response Formats                       | Standardize API responses (e.g., `200 OK: { success: true, data: {}}`).                                   | `GET /users/1` → `{ success: true, user: { id: 1, name: "Alice" } }`.                          |
|                            | Status Codes                           | Use [HTTP status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) for all API responses.    | `404 Not Found` for missing resources, `429 Too Many Requests` for rate limits.                |
|                            | Validation Rules                       | Apply consistent input validation (e.g., regex, length checks) across all endpoints.                      | All passwords must be `6–20 chars`, `1 uppercase`, `1 number`.                                   |
| **Behavioral Consistency** | Error Handling                         | Centralize error classes (e.g., `ValidationError`, `RateLimitError`) and handle them uniformly in clients.   | Throw `{ type: "ValidationError", field: "email", message: "... }`.                             |
|                            | Logging                                | Use structured logging (e.g., JSON) with standardized keys (`timestamp`, `level`, `message`).             | `{ "timestamp": "2024-05-20T12:00:00Z", "level": "error", "action": "login" }`.               |
|                            | Edge-Case Handling                     | Document and test common edge cases (e.g., empty inputs, concurrent operations) in all systems.            | Handle `null` user input in `update_profile()` with `DEFAULT_NAME = "Guest"`.                  |
| **Code/Architecture**      | Naming Conventions                     | Apply project-wide conventions (e.g., `PascalCase` for classes, `snake_case` for functions).               | Class: `UserRepository` → Function: `_sanitize_input()`.                                         |
|                            | Configuration                          | Externalize configs (e.g., `.env`, YAML) for environment-specific settings (e.g., `API_URL`).               | `.env` file: `DATABASE_URL=postgres://user:pass@localhost`                                      |
|                            | Dependency Management                  | Pin versions of dependencies (e.g., `package.json`, `requirements.txt`) to avoid compatibility issues.     | `react@18.2.0` → Not `react@latest`.                                                            |

---

## **Query Examples**
### **1. Frontend Query (UI Consistency Check)**
**Scenario:** Validate if all buttons use consistent styling.
**SQL-like Pseudocode:**
```sql
SELECT *
FROM ui_elements
WHERE type = 'button'
  AND (background_color NOT IN ('#0066cc', '#ccc')
       OR padding != 16px)
ORDER BY priority;
```

**Expected Output:**
| element_id | text      | background_color | padding | status      |
|------------|-----------|------------------|---------|-------------|
| btn_1      | Submit    | #0066cc          | 16px    | **✅ OK**   |
| btn_2      | Cancel    | #AACCFF          | 12px    | ❌ **Inconsistent** |

---
### **2. API Response Consistency Check**
**Scenario:** Verify all `/users` endpoints return consistent fields.
**Example Endpoint:**
```bash
GET /users/{id}  # Current response
GET /users/search?q=Alice  # Should match fields
```

**Expected Field Set (All Responses):**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "email": "string",
    "createdAt": "ISO8601"
  }
}
```

**Tooling Suggestion:**
Use **Postman Collections** or **OpenAPI/Swagger** validation to enforce this.

---
### **3. Error Handling Consistency Check**
**Scenario:** Ensure all backend errors include `errorCode` and `message`.
**Python Example:**
```python
def validate_input(data):
    if not data.get("email"):
        raise ValueError("400: Missing 'email' field")
    # ... other validations
```
**Expected Error Format (Across All Endpoints):**
```json
{
  "success": false,
  "error": {
    "code": "400",
    "message": "Missing 'email' field"
  }
}
```

---
### **4. Database Schema Consistency Check**
**Scenario:** Audit all tables for missing `createdAt` and `updatedAt` timestamps.
**SQL Query:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = tables.table_name
      AND column_name IN ('createdAt', 'updatedAt')
  );
```
**Expected Output:**
| table_name  |
|-------------|
| (empty)     |

---

## **Implementation Tools & Automation**
| **Tool**               | **Purpose**                                                                 | **Example Use Case**                                                                 |
|------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **ESLint/Prettier**    | Enforce code style consistency (e.g., quotes, indentation).                 | Auto-format React components to use `camelCase` props.                              |
| **Postman/Newman**     | Validate API response consistency across environments.                     | Test all endpoints with a `GET /health` call to ensure `200 OK` status.               |
| **Schema Registries**  | Document and enforce data contract consistency (e.g., Avro, Protobuf).     | Enforce all `user` objects to include `email` and `name` fields.                     |
| **CI/CD Checks**       | Fail builds if consistency rules are violated (e.g., missing `createdAt`).   | GitHub Actions: Run SQL audit before merging.                                         |
| **UI Testing Frameworks** | Automate UI consistency checks (e.g., Cypress, Playwright).           | Assert all buttons have matching `aria-label` attributes.                             |

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Risk**                                                                   | **Mitigation**                                                                       |
|---------------------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| Inconsistent API versions            | Breaking changes in undocumented fields.                                  | Use semantic versioning (`v1`, `v2`) and deprecation warnings.                       |
| UI/UX drift over time                | New features introduce inconsistent layouts.                              | Conduct quarterly UI audits with a styled guide.                                    |
| Undocumented edge cases              | Unhandled inputs lead to crashes.                                           | Document edge cases in a `CONTRIBUTING.md` file and run regression tests.           |
| Hardcoded values in code             | Maintenance nightmares when configs change.                                  | Externalize all configs (e.g., `APP_NAME` in `.env`).                                 |
| Lack of centralized error handling   | Inconsistent error messages across services.                               | Create a shared `Error` class with standardized formats.                            |

---

## **Related Patterns**
1. **[Single Source of Truth](https://www.martinfowler.com/bliki/SingleSourceOfTruth.html)**
   - *Why?* Ensures data consistency by centralizing authoritative data sources.
   - *How?* Apply this pattern to your database schema or a feature flag service.

2. **[Feature Flags](https://launchdarkly.com/blog/feature-flags-patterns/)**
   - *Why?* Allows gradual rollouts while maintaining UI/behavior consistency.
   - *How?* Use flags to toggle experimental flows without breaking existing ones.

3. **[CQRS (Command Query Responsibility Segregation)](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)**
   - *Why?* Separates read/write operations to enforce data consistency rules.
   - *How?* Apply to APIs where `GET /users` and `POST /users` have distinct schemas.

4. **[Immutable Data Models](https://www.freecodecamp.org/news/immutable-data-in-javascript/)**
   - *Why?* Prevents accidental mutations that break consistency.
   - *How?* Use `Immutable.js` (React) or `frozenset` (Python) for critical data.

5. **[Documentation as Code](https://www.documentationascode.org/)**
   - *Why?* Keeps API/UI docs in sync with implementation.
   - *How?* Use tools like **Swagger**, **Confluence**, or **Markdown** for living docs.

---
## **Further Reading**
- **"Designing Data-Intensive Applications"** (Martin Kleppmann) – Chapter on Consistency Models.
- **Google’s UI Design Principles** ([Material Design](https://m3.material.io/)) – Best practices for visual consistency.
- **RESTful API Best Practices** ([Microsoft Docs](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design)) – Data/API consistency.
- **ESLint Configs** ([Airbnb Style Guide](https://github.com/airbnb/javascript)) – Code consistency.