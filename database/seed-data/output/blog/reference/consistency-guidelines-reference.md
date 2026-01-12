**[Pattern] Consistency Guidelines: Reference Guide**

---

### **Overview**
Consistency Guidelines enforce design, behavior, and implementation uniformity across software systems, APIs, and user experiences. This pattern ensures predictable interactions, reduces cognitive load, and minimizes errors by defining reusable rules for naming conventions, error handling, data formatting, and UI/UX patterns.

Key benefits include:
- **Improved maintainability**: Standardized code and documentation reduce refactoring efforts.
- **Better UX**: Familiar patterns (e.g., button states, input validation) improve usability.
- **Scalability**: Clear guidelines allow teams to expand systems without breaking existing flows.
- **Auditability**: Consistent logging, error codes, and naming simplify debugging and compliance checks.

This guide covers schema requirements, implementation examples, and related patterns for adopting Consistency Guidelines effectively.

---

## **Schema Reference**

| **Category**               | **Attribute/Rule**                          | **Description**                                                                                     | **Examples/Constraints**                                                                                     |
|----------------------------|----------------------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Naming Conventions**     | Variable Names                               | Use camelCase for local variables, PascalCase for classes/types, and snake_case for database fields. | `userName`, `UserProfile`, `user_id`. Avoid abbreviations unless widely understood (e.g., `statusCode`).       |
|                            | API Endpoints                                | Use plural nouns for resources; sub-resources via `/{parent}/{child}`.                             | `/users/{id}/orders` (not `/user/{id}/order`).                                                          |
|                            | HTTP Methods                                 | RESTful verbs: `GET` (retrieve), `POST` (create), `PUT`/`PATCH` (update), `DELETE` (destroy).         | Avoid `GET` for updates; use `PATCH` for partial changes.                                                  |
| **Data Formatting**        | Response Payloads                           | Standardize JSON structure (e.g., `data: { ... }, errors: []`).                                   | ```json { "data": { "id": 1 }, "errors": [] } ``` (never omit `data`).                                  |
|                            | Timestamps                                   | Use ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DD`).                                         | `2023-10-15T14:30:00Z`, not `10/15/2023` or `Oct 15, 2023`.                                               |
|                            | Enums/Strings                               | Define allowed values in a shared schema (e.g., `user_status: ["active", "inactive", "banned"]`).   | Avoid hardcoded strings like `"YES"/"NO"`; use `active=false`.                                            |
| **Error Handling**         | Error Codes                                  | 3-digit HTTP-like codes (e.g., `400`, `500`) + descriptive messages.                                | `429: {"code": 429, "message": "Rate limit exceeded"}`.                                                   |
|                            | Validation Errors                           | Group errors by field; include `field`, `code`, and `message`.                                       | ```json { "errors": [{ "field": "email", "code": "invalid", "message": "Must contain '@" }] } ```.     |
| **UI/UX Patterns**         | Buttons                                      | Primary actions: `<button type="submit">`. Disabled states: `disabled` attribute.                 | ```html <button type="submit" disabled>Save</button> ```.                                               |
|                            | Input Validation                            | Show real-time feedback (e.g., `error`, `warning`, `success` classes).                             | Avoid silent failures; use ARIA labels for accessibility.                                                  |
|                            | Loading States                               | Use spinners or skeletons; disable interactive elements during loading.                            | ```html <div class="loading">Processing...</div> ```.                                                  |
| **Code Structure**         | Dependency Injection                        | Avoid global state; use constructor injection or service locators.                                   | Prefer `@Injectable` (Angular) or constructor DI (Spring) over singletons.                                |
|                            | Logging                                      | Standardize levels (`INFO`, `ERROR`, `DEBUG`) and format: `[TIME] [LEVEL] [SOURCE] message`.       | `2023-10-15T14:30:00 INFO auth-service: User login attempt failed`.                                       |
| **Documentation**          | API Specs                                    | Use OpenAPI/Swagger with `x-guidlines` extensions for pattern references.                           | Add `x-guidlines: { consistency: "use-pascal-case-for-types" }` to `swagger.json`.                         |
|                            | Internal Docs                                | Link to shared guidelines (e.g., `// See /docs/consistency.md for naming rules`).                  | Use `@see` tags (e.g., `@see /docs/consistency.md#naming`).                                               |

---

## **Implementation Details**

### **1. Defining Guidelines**
- **Collaborate Across Teams**: Involve front-end, back-end, and DevOps to align on critical areas (e.g., error codes, timestamps).
- **Versioning**: Tag guidelines by version (e.g., `v2.0`) to manage changes without breaking existing systems.
- **Enforcement Tools**:
  - **Linters**: ESLint (JavaScript), Pylint (Python) to enforce naming conventions.
  - **CI/CD**: Run validation scripts (e.g., `validate-api-specs.sh`) in pipelines.
  - **API Gateways**: Use tools like Kong or Apigee to enforce request/response schemas.

### **2. Example: API Response Consistency**
**Schema Rule**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "User Profile Response",
  "type": "object",
  "properties": {
    "data": { "type": "object", "required": true },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "field": { "type": "string" },
          "code": { "type": "string", "pattern": "^[0-9]{3}$" },
          "message": { "type": "string" }
        },
        "required": ["code", "message"]
      }
    }
  }
}
```

**Query Example (Success Response)**:
```http
GET /api/users/123
Status: 200 OK

{
  "data": {
    "id": 123,
    "name": "Alice",
    "email": "alice@example.com",
    "createdAt": "2023-01-15T09:00:00Z"
  },
  "errors": []
}
```

**Query Example (Error Response)**:
```http
POST /api/users
Status: 400 Bad Request

{
  "data": null,
  "errors": [
    {
      "field": "email",
      "code": "400",
      "message": "Email must contain '@'"
    }
  ]
}
```

### **3. Example: Front-End Button States**
**Schema Rule**:
```html
<!-- Button Component (React) -->
<button
  type="submit"
  class="consistency__button"
  disabled={isSubmitting}
  aria-busy={isSubmitting}
>
  {isSubmitting ? "Processing..." : "Submit"}
</button>
```

**Visual Consistency**:
- **Primary**: Blue background, white text.
- **Secondary**: Gray background, dark text (for non-actions like "Cancel").
- **Disabled**: Opacity `0.5`, cursor `not-allowed`.

### **4. Enforcing in Code**
**Python (Flask)**:
```python
from flask import jsonify

def validate_user_input(data):
    errors = []
    if "email" in data and "@" not in data["email"]:
        errors.append({
            "field": "email",
            "code": "400",
            "message": "Invalid email format"
        })
    return {"errors": errors} if errors else None

@app.route("/users", methods=["POST"])
def create_user():
    errors = validate_user_input(request.json)
    if errors:
        return jsonify({"data": None, **errors}), 400
    # Proceed with creation...
```

**JavaScript (Node.js)**:
```javascript
const { validate } = require("json-schema-validate");

const userSchema = {
  type: "object",
  properties: {
    name: { type: "string", minLength: 2 },
    email: { type: "string", pattern: "@.*" }
  },
  required: ["name", "email"]
};

app.post("/users", async (req, res) => {
  try {
    await validate(req.body, userSchema);
    // Proceed...
  } catch (err) {
    res.status(400).json({
      data: null,
      errors: [{ field: err.path, code: "400", message: err.message }]
    });
  }
});
```

---

## **Query Examples**

### **1. API Consistency Check**
**Request**:
```http
GET /api/v2/docs/consistency-check
Headers: { "Accept": "application/json" }
```

**Response (Success)**:
```json
{
  "status": "passed",
  "rules": [
    { "name": "endpoint-pluralization", "status": "passed" },
    { "name": "timestamp-format", "status": "passed" }
  ],
  "warnings": []
}
```

**Response (Failure)**:
```json
{
  "status": "failed",
  "rules": [
    { "name": "content-type-header", "status": "failed", "message": "Missing 'Content-Type' in POST /api/users" }
  ]
}
```

---

### **2. Front-End Validation**
**HTML/JS**:
```html
<form id="userForm" data-consistency="validate">
  <input type="email" name="email" required>
  <button type="submit">Submit</button>
</form>

<script>
  document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#userForm");
    form.addEventListener("submit", (e) => {
      const errors = Array.from(form.querySelectorAll("[data-consistency]"))
        .map(el => el.reportValidity());
      if (errors.some(e => !e.valid)) {
        e.preventDefault();
        alert("Please fix validation errors.");
      }
    });
  });
</script>
```

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                 | **How It Relates to Consistency Guidelines**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **[API Versioning]**             | Manage backward compatibility by versioning endpoints (e.g., `/api/v1/orders`). | Ensures new changes (e.g., new fields) don’t break existing clients; aligns with consistency in change management. |
| **[Postel’s Law (Robustness)]**  | "Be liberal in what you accept, strict in what you send."                       | Complements consistency by suggesting flexible input validation but strict output formatting.                 |
| **[Error Handling Best Practices]** | Standardize error codes, messages, and retries.                          | Uses consistency guidelines to define reusable error schemas (e.g., `429: RateLimitExceeded`).                 |
| **[Schema as Contract]**          | Define API contracts via OpenAPI/Swagger.                                    | Schema rules (e.g., field types, examples) extend consistency to machine-readable contracts.                   |
| **[Feature Flags]**               | Control feature rollouts without deployment.                                  | Ensures consistent behavior across flagged/unflagged states (e.g., disabled buttons, hidden fields).          |
| **[Internationalization (i18n)]** | Localize content without hardcoding languages.                             | Requires consistent placeholder keys (e.g., `error.email.invalid`) and fallbacks for missing translations.    |

---

## **Best Practices**
1. **Start Small**: Begin with critical areas (e.g., error handling, naming) before expanding to UI patterns.
2. **Document Exceptions**: List when rules can be broken (e.g., legacy systems) and justify them.
3. **Automate Enforcement**: Integrate checks into CI/CD (e.g., fail builds for schema violations).
4. **Review Regularly**: Update guidelines quarterly to reflect new tools/standards (e.g., web components).
5. **Provide Examples**: Include live demos (e.g., [Consistency Playground](https://example.com/consistency)) for quick reference.