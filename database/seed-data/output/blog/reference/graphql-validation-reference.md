# **[Pattern] GraphQL Validation Reference Guide**

---

## **Overview**
GraphQL Validation is a critical pattern ensuring data integrity by enforcing rules on input queries, mutations, and schema definitions before execution. Unlike REST, where invalid requests often return errors, GraphQL validates at the parser level, rejecting malformed or dangerous queries early. This pattern covers schema-level validation (via SDL), runtime argument validation, and custom directives to maintain consistency, security, and performance. Validation prevents common issues like:
- **Over-fetching/under-fetching** (due to unchecked selections).
- **Unexpected mutations** (e.g., unauthorized operations).
- **Data corruption** (invalid types or constraints).

By combining declarative schema constraints with imperative runtime checks, GraphQL Validation balances flexibility with strict control over data flows.

---

## **Core Principles**
GraphQL validation operates on three layers:
1. **Parser Layer**: Checks syntax and basic structure (e.g., valid field names).
2. **Schema Layer**: Enforces type consistency and relationships (e.g., required fields).
3. **Runtime Layer**: Validates dynamic inputs (e.g., argument constraints, business rules).

---
## **Schema Reference**

### **1. Built-in Validation Rules (GraphQL Core)**
| Rule                     | Description                                                                                                                                 | Example Violations                          |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Known Type**           | Fields/mutations must reference valid types in the schema.                                                                                   | `{ user(id: "123", name: "Alice" }` (if `name` isn’t a field). |
| **Variables Are Scalars** | Query variables must map to scalar types (unless using `InputType`).                                                                         | `{ user(id: "123", tags: ["admin"]) }` (if `tags` is non-scalar). |
| **Unique Field Names**   | Duplicate field names in a selection are rejected.                                                                                           | `{ user { id email } { id phone } }`        |
| **Field Existence**      | Fields must exist on their parent type.                                                                                                       | `{ user(age: 25) { nonExistentField } }`   |
| **Correct Arguments**    | Provided arguments must match field definitions (type, required status).                                                                | `{ login(username: 123) }` (if `username` expects `String`). |
| **Fragments Must Match** | Fragment spread types must align with referenced types.                                                                                   | `fragment on User { ...InvalidFragment }`   |
| **Variable Usages**      | Variables must be used in queries with compatible types.                                                                                   | `{ user(id: $age) }` (if `$age` is `Int` but `id` is `ID`). |
| **Provided Defaults**    | Default values must match field types.                                                                                                      | `{ user(id: "123", status: 100) }` (if `status` expects `String`). |

---

### **2. Custom Validation Directives**
Extend validation with custom directives (requires `@deprecated` or custom implementations via plugins like [`graphql-tools`](https://www.graphql-tools.com/)).

| Directive               | Purpose                                                                                     | Example Usage                          |
|-------------------------|---------------------------------------------------------------------------------------------|----------------------------------------|
| `@require`              | Enforces a field/mutation is present (e.g., for authentication).                            | `type Mutation { login(email: String! @require): Boolean }` |
| `@enumValues`           | Restricts enum values to a subset (e.g., allow only "active" status).                      | `enum UserStatus { ACTIVE, INACTIVE }` → `@enumValues(["ACTIVE"])` |
| `@maxLength`            | Limits string length (e.g., passwords < 64 chars).                                           | `input Password { value: String! @maxLength(64) }` |
| `@validate` (custom)    | Runs arbitrary validation logic (e.g., regex checks).                                       | `@customDirective("validatePassword")` |

**Note**: Custom directives require a validator plugin or schema modifiers (e.g., Apollo’s [`graphql-tools`](https://www.apollo.dev/blog/building-custom-directives-for-graphql)).

---

### **3. Mutation Validation**
Mutations require stricter checks to prevent data loss. Common rules:
- **Authorization**: Ensure users have permissions (e.g., `@auth`).
- **Idempotency**: Reject duplicate operations (e.g., `@idempotencyKey`).
- **Referential Integrity**: Validate foreign keys (e.g., `userId` exists in `users` table).

**Example Schema Snippet**:
```graphql
type Mutation {
  updateUser(
    id: ID!
    data: UserInput!
    @auth(requires: ADMIN)
    @validate("data.email matches /^[^\s@]+@[^\s@]+\.[^\s@]+$/")
  ): User
}
```

---
## **Query Examples**

### **1. Valid Query**
```graphql
query GetUser($userId: ID!) {
  user(id: $userId) {
    id
    name
    email @require
    posts(limit: 10) {
      title
    }
  }
}
```
**Variables**:
```json
{ "userId": "123" }
```
**Why Valid**:
- All fields (`id`, `name`, `email`) exist on `User`.
- `@require` ensures `email` is returned (even if empty).
- `posts` uses a valid argument (`limit`).

---

### **2. Invalid Query (Missing Field)**
```graphql
query InvalidQuery {
  user(id: "123") {
    id
    nonExistentField  # ❌ Fails: `nonExistentField` doesn’t exist on `User`.
  }
}
```
**Error**:
```
Validation Error: Cannot query field "nonExistentField" on type "User".
```

---

### **3. Invalid Mutation (Authorization)**
```graphql
mutation UpdateUser {
  updateUser(
    id: "123",
    data: { name: "Bob" }
    # Missing @auth directive (or user lacks permissions)
  ) {
    id
  }
}
```
**Error** (if using `@auth`):
```
Validation Error: Mutation "updateUser" requires ADMIN permissions.
```

---

### **4. Custom Validation Failure**
```graphql
mutation SetPassword {
  updateUser(
    id: "123",
    data: { password: "short" }  # ❌ Fails: `@maxLength(8)` directive.
  ) {
    id
  }
}
```
**Error**:
```
Validation Error: Password must be at least 8 characters long.
```

---
## **Implementation Details**

### **1. Schema Definition**
Define validation rules in your schema (SDL) or via code-generators (e.g., GraphQL Code Generator).

**Example SDL with Directives**:
```graphql
directive @auth(requires: UserRole!) on FIELD_DEFINITION
directive @maxLength(length: Int!) on FIELD_DEFINITION

enum UserRole { ADMIN, EDITOR, GUEST }

input UserInput {
  name: String @maxLength(50)
  email: String @maxLength(64)
}

type Mutation {
  updateUser(
    id: ID!
    data: UserInput!
    @auth(requires: ADMIN)
  ): User
}
```

---
### **2. Runtime Validation**
Use libraries like:
- **Apollo Server**: Built-in validation with plugins (e.g., [`graphql-validation-extensions`](https://www.apollo.dev/blog/graphql-validation-extensions)).
- **GraphQL Yoga**: Supports custom validators via middleware.
- **Custom Engines**: Implement `ValidationContext` for advanced logic.

**Example (Apollo Server Plugin)**:
```javascript
const { ApolloServer } = require("apollo-server");
const { createValidationRule } = require("graphql-validation-extensions");

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    createValidationRule({
      rule: ({ document }) =>
        document.definitions.some(def =>
          def.kind === "OperationDefinition" && def.name?.value === "query"
        ),
      message: "Queries must include a name.",
    }),
  ],
});
```

---
### **3. Testing Validation**
Test validation with tools like:
- **GraphQL Playground**: Manually submit invalid queries.
- **Jest + `graphql-validation`](https://github.com/graphql/graphql-js/blob/master/src/utilities/ValidationRule.js)**: Unit-test rules.
- **Schematic**: Validate SDL pre-deployment.

**Example Jest Test**:
```javascript
const { validate } = require("graphql");
const { graphqlSync } = require("graphql");

test("rejects missing required field", () => {
  const schema = buildSchema(`
    type Query { user(id: ID!): User }
    type User { id: ID! email: String! }
  `);
  const query = `query { user(id: "1") { id } }`;
  const errors = validate(schema, query);
  expect(errors).toHaveLength(1);
});
```

---
## **Related Patterns**

| Pattern                          | Description                                                                                                                                 | Integration with Validation                          |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **[GraphQL Persisted Queries](...)** | Compile queries at build-time to reduce runtime overhead.                                                                                | Pre-validates queries before execution.              |
| **[GraphQL Subscriptions](...)**   | Real-time updates via WebSockets.                                                                                                          | Validates subscription payloads (e.g., event filters). |
| **[Query Complexity Analysis](...)** | Limits query depth/width to prevent denial-of-service.                                                                                     | Works alongside schema validation for performance.  |
| **[GraphQL Persisted Queries](...)** | Cache queries as hashes to reduce network load.                                                                                          | Validates persisted queries during registration.    |
| **[GraphQL Error Handling](...)**  | Structured error reporting (e.g., `errors` in responses).                                                                                 | Validation errors propagate as part of response.   |

---
## **Best Practices**
1. **Fail Fast**: Reject invalid queries at parse time where possible.
2. **Declarative First**: Use schema directives (`@require`, `@auth`) over runtime checks.
3. **Standardize Errors**: Return consistent error shapes (e.g., `{ errors: [{ path, message }] }`).
4. **Document Constraints**: Annotate inputs with rules (e.g., `@maxLength` in SDL).
5. **Test Edge Cases**: Validate empty inputs, null values, and type mismatches.
6. **Use Tools**: Leverage Apollo Studio, GraphQL Inspector, or `graphql-cli` for schema analysis.

---
## **Troubleshooting**
| Issue                          | Cause                                                                 | Solution                                                                 |
|--------------------------------|------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Validation skipped**         | Missing `validationRules` in server config.                           | Add `validationRules` to Apollo/Yoga server.                             |
| **Custom directive not working** | Directive not registered in schema.                                     | Use `makeSchema` with custom directives (e.g., `makeExecutableSchema`). |
| **Performance bottlenecks**    | Overly complex validation logic.                                       | Offload checks to resolvers or use `@skip` to short-circuit.             |
| **False positives**            | Overly strict rules (e.g., `@require` on optional fields).             | Adjust rules or use `@deprecated` for legacy fields.                     |

---
## **References**
- [GraphQL Specification: Validation](https://spec.graphql.org/October2021/#sec-VALIDATION)
- [Apollo Directive Guide](https://www.apollo.dev/docs/apollo-server/schema/directives/)
- [GraphQL Validation Extensions](https://www.apollo.dev/blog/graphql-validation-extensions)
- [GraphQL Code Generator](https://www.graphql-code-generator.com/) (for schema-based validation)