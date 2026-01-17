# **[Pattern] Schema Artifacts Generation Reference Guide**

---

## **1. Overview**
The **Schema Artifacts Generation** pattern ensures that a GraphQL compilation pipeline yields actionable outputs beyond the core schema definition. By generating **three key artifacts**—**CompiledSchema (execution plan), GraphQL SDL (client-facing schema), and validation reports (developer feedback)**—this pattern enables optimized query resolution, maintainable client integrations, and proactive error handling.

This guide covers how to implement, configure, and leverage these artifacts in a GraphQL service. The pattern is critical for production-grade systems requiring **performance, clarity, and traceability**.

---

## **2. Key Concepts**

| **Term**               | **Description**                                                                                     | **Use Case**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **GraphQL SDL**         | Standard Definition Language syntax (`.graphql` file) for declarative schema definition.           | Client libraries, IDE tooling, and documentation tools (e.g., GraphQL Playground).               |
| **CompiledSchema**      | A pre-processed, optimized execution plan (e.g., via `graphql-js` compiler or custom runtime).     | Runtime efficiency, caching, and advanced query parsing.                                         |
| **Validation Reports**  | Structured logs/deliverables highlighting schema issues (e.g., missing directives, ambiguous types). | Developer workflows (CI/CD, onboarding, or refactoring).                                         |

---

## **3. Schema Reference**

### **3.1 Input: Schema Definition File (`.graphql`)**
```graphql
# Example: schema.graphql
type Query {
  user(id: ID!): User @deprecated
  posts: [Post!]!
}

type User {
  id: ID!
  name: String!
}

type Post {
  id: ID!
  title: String!
  author: User! @requires("auth")
}
```

**Key Attributes:**
- **Directives:** `@deprecated`, `@requires` (custom logic for authorization/filtering).
- **Non-nullable Fields:** `!` indicators enforce runtime validation.
- **Custom Scalars:** Extend with `scalars` for non-JSON types (e.g., `DateTime`).

---

### **3.2 Artifacts Output**

| **Artifact**       | **Format**               | **Tools/Libraries**                          | **Example Output**                                                                                     |
|--------------------|--------------------------|-----------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **GraphQL SDL**    | Text/JSON (SDL1/SDL2)    | `graphql-tools`, `graphql-sdl`               | ```json { "types": [ { "name": "Query", "fields": [...] } ] } ```                                       |
| **CompiledSchema** | Binary/Serialized JSON   | `graphql-compiler`, custom runtime plugins   | Optimized AST with resolved directives, type hints, and validation hooks.                             |
| **Validation**     | Structured Log File      | `graphql-validator`, custom scripts           | ```json { "errors": [ { "path": ["Query.user"], "message": "Deprecated field" } ] } ```               |

---

## **4. Implementation Steps**

### **4.1 Generate GraphQL SDL**
Use a schema transformer to export the SDL for clients:
```bash
# Using graphql-cli
graphql-cli compile --schema schema.graphql --output ./client/sdl.js
```
**Output:** `./client/sdl.js` (ES6 module for client-side use).

---

### **4.2 Compile to Execution Plan**
Leverage a GraphQL compiler to generate a **CompiledSchema** with:
- **Directive Resolution:** Expand `@requires` into middleware wrappers.
- **Caching:** Pre-compute field resolvers for hot paths.

```javascript
// Example: Custom compiler (pseudo-code)
const { compileSchema } = require('graphql-compiler');

const compiled = compileSchema({
  schema: readFileSync('./schema.graphql'),
  hooks: { onResolveDirective: (directive) => { /* add auth checks */ } }
});

fs.writeFileSync('./dist/compiled-schema.js', JSON.stringify(compiled));
```

---

### **4.3 Validate Schema**
Run a validator to flag issues before deployment:
```bash
# Using graphql-validator
graphql-validator validate ./schema.graphql --output ./reports/validation.json
```
**Example Report:**
```json
{
  "warnings": [
    { "type": "deprecated", "field": "Query.user" }
  ],
  "errors": [
    { "type": "ambiguous", "field": "Post.author" }
  ]
}
```

---

## **5. Query Examples**

### **5.1 SDL-Based Query (Client-Side)**
```javascript
// Using SDL to build queries dynamically
const { buildQuery } = require('./client/sdl');
const query = buildQuery(`
  query GetUser($id: ID!) {
    user(id: $id) {
      name
    }
  }
`);
```

### **5.2 CompiledSchema Optimization**
```javascript
// Optimized resolver lookup
const compiled = require('./dist/compiled-schema');
const { resolve } = compiled;

const result = await resolve({
  schema: compiled,
  query: '{ user(id: "123") { name } }',
  context: { user: { id: "123" } }
});
```

---

## **6. Configuration**

### **6.1 Custom Compiler Hooks**
Extend the compiler for domain-specific logic:
```javascript
const hooks = {
  onResolveDirective: (directive) => {
    if (directive.name === 'requires') {
      return { middleware: authMiddleware };
    }
  }
};
```

### **6.2 Validation Rules**
Define custom rules in `validation-config.yml`:
```yaml
rules:
  - type: DEPRECATED_FIELD
    path: Query.user
  - type: AMBIGUOUS_TYPE
    fields: [Post.author]
```

---

## **7. Query Examples (Interactive Playground)**
```graphql
# Example: Query with SDL
query {
  posts {
    title
    author {
      name
    }
  }
}
```

**Response (with CompiledSchema):**
```json
{
  "data": {
    "posts": [
      { "title": "Hello", "author": { "name": "Alice" } }
    ]
  }
}
```

---

## **8. Troubleshooting**
| **Issue**               | **Solution**                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------|
| Missing SDL output       | Ensure `graphql-cli` is installed and flags are correct.                                         |
| Validation errors        | Check `validation-config.yml` for misconfigured rules.                                           |
| Compilation failure      | Review custom hooks for syntax errors in directive resolution.                                   |

---

## **9. Related Patterns**
1. **[Schema Stitching](...):** Combine multiple schemas into a unified artifact.
2. **[Directives as Features](...):** Use `@requires`/`@deprecated` for runtime logic.
3. **[Schema Evolution](...):** Handle backward compatibility via artifact versioning.

---
**Final Notes:**
- **Tooling:** Supports `graphql-tools`, `graphql-cli`, and custom compilers.
- **Best Practice:** Store artifacts in a versioned directory (e.g., `./dist/v1/`).
- **Extensibility:** Hooks allow adding analytics (e.g., query performance telemetry).

---
**Length:** ~1,000 words. Adjust sections as needed for deeper dives (e.g., advanced compiler plugins).