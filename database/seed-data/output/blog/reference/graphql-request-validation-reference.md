# **[Pattern] GraphQL Request Validation – Reference Guide**

---

## **Overview**
GraphQL request validation ensures that client queries, mutations, and subscriptions adhere to a defined schema (`CompiledSchema`). This pattern enforces structural integrity by validating:
- **Valid operation types** (Query, Mutation, Subscription)
- **Existence of declared types and fields**
- **Correct argument types and cardinality** (required, nullable, lists)
- **Type compatibility** (e.g., scalar values matching field expectations)
- **Directive applicability and arguments**

Failure to validate results in a `GraphQLValidationError`, providing clear feedback for debugging. This guide covers implementation details, schema constraints, query examples, and related patterns.

---

## **Key Concepts & Schema Reference**

### **Validation Rules**
GraphQL enforces the following during request parsing:

| **Rule**                          | **Description**                                                                 | **Example of Validation**                          |
|------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------------|
| **Operation Type**                | Must match allowed types in `schema` (Query, Mutation, Subscription).          | ✅ `query { user(id: 1) }` (valid if `Query` allows it). |
| **Field Existence**               | Fields must be declared in their parent type.                                   | ❌ `query { nonExistentField }` → Error.          |
| **Argument Requirements**         | Arguments must match declared input types (type, nullability, constraints).     | ✅ `mutation { createUser(name: "Alice", age: 25)}` |
| **Fragment Resolution**           | Fragment spreads must reference valid types/fields.                              | ✅ `fragment UserFragment on User { ...`, with matching type. |
| **Variables Alignment**           | Variable names/types must match the operation’s variable definitions.          | ❌ `query($id: Int) { user(id: $name) }` → Error.   |
| **Directives**                    | Must be applicable to the node type and have valid arguments.                    | ✅ `@deprecated(reason: "Legacy field")` on a field. |
| **Type System**                   | Scalar/literal values must conform to field types (e.g., `Int` vs. `String`).    | ❌ `query { user(age: "25") }` (passes as `String`). |

---

### **Schema Reference Table**
The following table outlines validated components in a `CompiledSchema`:

| **Schema Component**       | **Validation Details**                                                                                     | **Error Case Example**                          |
|----------------------------|------------------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Operation Definition**   | Must specify at least one of `query`, `mutation`, or `subscription`.                                       | ❌ Missing operation type.                      |
| **Type Definition**        | Types must be fully defined before use (objects, inputs, unions, interfaces, enums, scalars).             | ❌ Referencing `User` before its `type` declaration. |
| **Field Declaration**      | Fields must include: name, type, args (if any), directives, and return type constraints.                   | ❌ `type Query { user: Int! }` → Error (non-field type). |
| **Input Type (Arguments)** | Input fields must declare type, nullability, and default values.                                             | ❌ `input CreateUser { name: }` → Missing type.   |
| **Scalar Types**           | Built-in (`Int`, `String`, etc.) and custom scalars must be parsed correctly.                               | ❌ Custom scalar `Date` with invalid format.      |
| **Enum Values**            | Allowed enum values must match declared variants.                                                          | ❌ `UserRole { ADMIN, EDITOR, GUEST }` → `"MANAGER"` invalid. |
| **Directive Usage**        | Directives must be valid for their target (e.g., `@deprecated` on fields, not arguments).                   | ❌ `@deprecated` on an input type.               |
| **Variable Definitions**   | Variable types must match their usage in the operation.                                                       | ❌ `query($id: String) { user(id: $id) }` if `user(id: Int)`. |

---

## **Query Validation Examples**

### **1. Valid Query (Success Case)**
```graphql
query GetUser($id: ID) {
  user(id: $id) {
    id
    name
    age
  }
}
```
**Variables:**
```json
{ "id": "123" }
```
- **Validation Passes**: `user` field exists in `Query`, `id` argument aligns with `ID` type.

---

### **2. Invalid Query (Missing Field)**
```graphql
query {
  user {
    nonexistentProperty
  }
}
```
**Error Output:**
```json
{
  "errors": [
    {
      "message": "Cannot query field 'nonexistentProperty' on type 'User'.",
      "locations": [{ "line": 3, "column": 7 }]
    }
  ]
}
```
- **Cause**: The `User` type does not declare `nonexistentProperty`.

---

### **3. Type Mismatch (String vs. Int)**
```graphql
query {
  user(age: "thirty") {
    name
  }
}
```
**Error Output:**
```json
{
  "errors": [
    {
      "message": "Variable '$age' got invalid value 'thirty'. Expected type 'Int'.",
      "locations": [{ "line": 2, "column": 9 }]
    }
  ]
}
```
- **Cause**: The `age` argument expects an `Int`, but a `String` was provided.

---

### **4. Fragment Resolution Error**
```graphql
fragment UserDetails on User {
  email
  address
}

query {
  user(id: 1) {
    ...UserDetails
    nonexistentField
  }
}
```
**Error Output:**
```json
{
  "errors": [
    {
      "message": "Cannot query field 'nonexistentField' on type 'User'.",
      "locations": [{ "line": 8, "column": 7 }]
    }
  ]
}
```
- **Cause**: The fragment resolves to valid fields, but the parent query includes an undefined field.

---

### **5. Directive Misuse**
```graphql
type Query {
  user(id: ID): User @deprecated(reason: "Use 'findUser' instead")
}

query {
  user(id: 1)
}
```
**Error Output:**
*(No syntax error; directive is valid but logged as a warning in some implementations.)*

---
**Validation Note**: While directives rarely cause parsing errors, they may influence execution behavior (e.g., deprecation warnings).

---

## **Implementation Details**

### **Validation Phases**
GraphQL validation occurs in stages. Clients must pass requests through the following:
1. **Syntax Validation** (ensure parser input is valid GraphQL syntax).
2. **Schema Validation** (check against `CompiledSchema` for fields, types, etc.).
3. **Argument Validation** (type-check variables against declared inputs).
4. **Fragment Resolution** (validate spread fragments reference existing types/fields).
5. **Directive Validation** (ensure directives are applicable to the node).

---
### **Custom Validation (Advanced)**
Extend validation with custom rules via `GraphQLVisitor` or plugins (e.g., [graphql-validation-extensions](https://github.com/graphql/graphql-js#extending-validation)):
```javascript
const CustomValidationRule = {
  validate(_, { schema, document }) {
    document.definitions.forEach(def => {
      if (def.kind === 'OperationDefinition') {
        const { operation } = def;
        if (operation === 'mutation' && !def.selectionSet.selections.some(s => s.name.value === 'createUser')) {
          throw new GraphQLValidationError('Mutations must include createUser operation.');
        }
      }
    });
  },
};
```

---
### **Performance Considerations**
- **Pre-compile Schema**: Use `graphql-tools` or Apollo Server to generate a `CompiledSchema` for faster validation.
- **Incremental Validation**: Reuse validation results for repeated queries (e.g., in GraphQL APIs with caching).
- **Client-Side Validation**: Implement lightweight checks (e.g., with [graphql-codegen](https://graphql-codegen.com/)) to catch errors before sending requests.

---

## **Query Examples: Common Pitfalls**

| **Scenario**                     | **Example Query**                          | **Validation Error**                          |
|----------------------------------|--------------------------------------------|-----------------------------------------------|
| **Null Argument Error**          | `query { user(id: null) }` where `id: ID!` | Missing required argument.                   |
| **Variable Scope Mismatch**      | `query($id: Int) { ... ($id: $name) }`    | `$name` undefined, `$id` unused.             |
| **Non-nullable Field Omission**  | `query { user { name: null } }` (if `name: String!`) | Cannot return `null` for non-nullable field. |
| **List Cardinality**             | `query { users { email } }` where `email: [String]!` | Missing required list items.                 |

---

## **Related Patterns**
1. **[GraphQL Schema Stitching](https://www.apollographql.com/docs/apollo-server/schema/stitching/)**
   - Combine multiple schemas; validate requests against the merged `CompiledSchema`.
2. **[GraphQL Persisted Queries](https://www.apollographql.com/docs/apollo-server/performance/persisted-queries/)**
   - Pre-validate queries at parse time to reduce runtime checks.
3. **[GraphQL Directives](https://graphql.github.io/graphql-spec/directives/)**
   - Use `@deprecated`, `@skip`, and `@include` for conditional validation.
4. **[GraphQL Subscriptions](https://www.apollographql.com/docs/apollo-server/data/subscriptions/)**
   - Validate subscription messages with the same rules as queries.
5. **[GraphQL Error Handling](https://graphql.github.io/graphql-spec/errors/)**
   - Structure errors to include `path`, `locations`, and `extensions` for debugging.

---
## **Tools & Libraries**
| **Tool**                          | **Purpose**                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| [graphql-tools](https://www.graphql-tools.com/) | Schema compilation and validation utilities.                                |
| [Apollo Server](https://www.apollographql.com/docs/apollo-server/) | Built-in validation with custom plugins.                                   |
| [graphql-language-service](https://github.com/GraphQLLanguageService/graphql-language-service) | VS Code/IDE support for real-time validation.                           |
| [graphql-validate](https://www.npmjs.com/package/graphql-validate) | Standalone validation library.                                              |

---
## **Best Practices**
1. **Define Clear Schemas**: Use tools like [GraphQL Code Generator](https://graphql-codegen.com/) to auto-generate type-safe clients.
2. **Leverage Directives**: Use `@deprecated` to flag obsolete fields and warn clients early.
3. **Validate Early**: Use client-side frameworks (e.g., Apollo Client) to validate before sending requests.
4. **Document Fields**: Include `description` fields in schema to clarify validation expectations.
5. **Monitor Errors**: Log validation errors to track schema drift or client misuse.

---
## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                     |
|-------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| "Unknown type" error               | Client queries a type not in the schema.                                      | Update schema or client query.                  |
| "Variable not used" warning        | Variables are defined but unused.                                             | Remove unused variables or update the query.     |
| "Cannot return null" error         | Non-nullable field returns `null` in resolvers.                              | Adjust resolver to return a valid value.         |
| Fragment spread validation failure | Fragment references undefined fields.                                         | Fix fragment spreads or update referenced types. |

---
**Final Note**: GraphQL validation ensures consistency between client and server schemas. By adhering to this pattern, you reduce runtime errors and improve developer experience. For further reading, consult the [GraphQL Specification](https://spec.graphql.org/June2018/).