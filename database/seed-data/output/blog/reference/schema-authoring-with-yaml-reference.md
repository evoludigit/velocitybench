# **[Pattern] YAML-Based Schema Authoring: Reference Guide**

---

## **Overview**
YAML-based schema authoring is a structured approach to defining GraphQL schemas using **YAML**, a human-readable, language-agnostic format. This pattern is ideal for:
- **Configuration-driven workflows** (e.g., CI/CD, multi-environment setups)
- **Multi-language teams** (YAML is widely supported across programming languages)
- **Collaborative schema design** (tools like VS Code with YAML plugins provide validation and autocomplete)
- **Externalized schema management** (e.g., storing schemas in Git, version-controlled configs)

This guide covers how to define GraphQL schemas in YAML, including syntax, validation, and integration with GraphQL servers. While YAML itself doesn’t generate GraphQL types directly, tools like [`graphql-yaml`](https://www.npmjs.com/package/graphql-yaml) or custom scripts can transform YAML into a GraphQL SDL (Schema Definition Language).

---

## **Core Concepts**
### **1. Key Files**
| File          | Purpose                                                                 |
|---------------|-------------------------------------------------------------------------|
| `graphql.yml` | Root schema definition file (optional, for organization).               |
| `*.yaml`      | Nested schema definitions (e.g., `types/user.yaml`, `queries/auth.yaml`).|
| `schema.graphql` | Generated GraphQL SDL (output of YAML-to-SDL conversion).             |

### **2. YAML Schema Anatomy**
A YAML-defined schema consists of:
- **Types** (`object`, `interface`, `union`, `enum`, `scalar`)
- **Directives** (e.g., `@deprecated`, `@auth`)
- **Queries/Mutations** (resolvers or placeholder functions)
- **Inputs** (for arguments)

---

## **Schema Reference**
Below is the **YAML schema syntax** for defining GraphQL types and queries. Each section maps 1:1 to GraphQL SDL.

---

### **1. Defining Types**
#### **Object Type**
```yaml
type: Object
name: User
description: Represents a registered user.
fields:
  - name: id
    type: ID!
    description: Unique user identifier.
  - name: email
    type: String!
    description: User's email address.
    directives:
      - name: auth
        args:
          require: ADMIN_OR_USER
```

#### **Interface**
```yaml
type: Interface
name: Entity
description: Base interface for all entities.
fields:
  - name: createdAt
    type: DateTime!
```

#### **Union**
```yaml
type: Union
name: SearchResult
possibleTypes:
  - User
  - Product
```

#### **Enum**
```yaml
type: Enum
name: Role
values:
  - name: ADMIN
    description: Full access privileges.
  - name: USER
    description: Standard user access.
```

#### **Input Object**
```yaml
type: Input
name: FilterUserInput
fields:
  - name: role
    type: Role
  - name: emailContains
    type: String
```

---

### **2. Queries and Mutations**
#### **Query**
```yaml
query: GetUser
description: Retrieves a user by ID.
args:
  - name: id
    type: ID!
output:
  type: User
  resolver: "src/resolvers/user.js#getUser"
```

#### **Mutation**
```yaml
mutation: CreateUser
description: Registers a new user.
args:
  - name: input
    type: CreateUserInput!
output:
  type: User
  resolver: "src/resolvers/user.js#createUser"
```

---

### **3. Directives**
```yaml
directive:
  - name: auth
    args:
      - name: require
        type: Role!
        default: USER
    locations:
      - FIELD_DEFINITION
      - OBJECT
      - QUERY
```

---

### **4. Scalars (Custom)**
```yaml
scalar: DateTime
description: Custom scalar for ISO 8601 timestamps.
parser: "src/scalars/dateTime.js#parseValue"
serialize: "src/scalars/dateTime.js#serialize"
```

---

## **Query Examples**
### **Example 1: Fetch a User**
**YAML Query Definition:**
```yaml
query: GetUserByEmail
args:
  - name: email
    type: String!
output:
  type: User
  resolver: "src/resolvers/user.js#getUserByEmail"
```

**Generated GraphQL:**
```graphql
query GetUserByEmail($email: String!) {
  getUserByEmail(email: $email) {
    id
    email
    role
  }
}
```

**Execution (GraphQL Variables):**
```json
{ "email": "user@example.com" }
```

---

### **Example 2: Search with Union**
**YAML Query Definition:**
```yaml
query: SearchEntities
args:
  - name: query
    type: String!
  - name: type
    type: SearchType
output:
  type: [SearchResult]!
```

**Generated GraphQL:**
```graphql
query SearchEntities($query: String!, $type: SearchType) {
  searchEntities(query: $query, type: $type) {
    ... on User {
      id
      email
    }
    ... on Product {
      id
      name
    }
  }
}
```

**Execution:**
```json
{ "query": "john", "type": "USER" }
```

---

## **Validation Rules**
| Rule                          | Example Violations                          | Tool Support                          |
|-------------------------------|---------------------------------------------|---------------------------------------|
| Required fields               | Missing `name` in a type definition.        | `js-yaml` + custom validators.        |
| Unique type names             | Duplicate `User` type in `users.yaml`.      | Schema linter (e.g., `graphql-yaml`). |
| Valid resolver paths          | Broken resolver reference (`nonexistent.js`).| CI checks (e.g., ESLint).             |
| YAML syntax                   | Unquoted special chars (`email: user@.com`). | YAML linters (e.g., `yamllint`).       |

---

## **Implementation Steps**
### **1. Convert YAML to GraphQL SDL**
Use a tool like [`graphql-yaml`](https://github.com/graphql-yaml/graphql-yaml):
```bash
npx graphql-yaml graphql.yml > schema.graphql
```

### **2. Integrate with a GraphQL Server**
- **Apollo Server**:
  ```javascript
  const { makeExecutableSchema } = require('@graphql-tools/schema');
  const fs = require('fs');
  const schema = makeExecutableSchema({
    typeDefs: fs.readFileSync('./schema.graphql', 'utf8'),
    resolvers: require('./resolvers.js'),
  });
  ```
- **GraphQL Core**:
  Parse `schema.graphql` directly with `graphql/language/parser`.

### **3. CI/CD Validation**
Add pre-commit hooks to validate YAML schema:
```yaml
# .pre-commit-config.yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  hooks:
    - id: yaml-lint
- repo: local
  hooks:
    - id: graphql-yaml-validate
      name: Validate GraphQL YAML
      entry: npx graphql-yaml schema.yml --validate
      language: system
```

---

## **Query Examples (Advanced)**
### **Example 3: Nested Queries**
**YAML:**
```yaml
query: GetUserOrders
args:
  - name: userId
    type: ID!
output:
  type: [Order]
  resolver: "src/resolvers/order.js#getUserOrders"
```

**Generated GraphQL:**
```graphql
query GetUserOrders($userId: ID!) {
  getUserOrders(userId: $userId) {
    id
    user {
      id
      email
    }
  }
}
```

---

### **Example 4: Mutation with Input**
**YAML:**
```yaml
mutation: UpdateUserProfile
args:
  - name: input
    type: UpdateUserProfileInput!
output:
  type: User
  resolver: "src/resolvers/user.js#updateProfile"
```

**Generated GraphQL:**
```graphql
mutation UpdateUserProfile($input: UpdateUserProfileInput!) {
  updateUserProfile(input: $input) {
    email
    role
  }
}
```

**Variables:**
```json
{
  "input": {
    "email": "new@example.com",
    "role": "ADMIN"
  }
}
```

---

## **Related Patterns**
| Pattern                          | Description                                                                 | Use Case                                  |
|----------------------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **[Schema Stitching]**           | Combine multiple YAML schemas into a unified GraphQL schema.               | Microservices federation.                 |
| **[GraphQL Modules]**            | Split YAML schemas by domain (e.g., `auth.yaml`, `products.yaml`).        | Large-scale applications.                 |
| **[Versioned Schemas]**          | Maintain parallel YAML schemas for backward compatibility.                 | Legacy system migration.                  |
| **[Task Automation]**            | Use YAML schemas to generate API clients (e.g., with `graphql-codegen`).  | Developer tooling.                       |
| **[Schema-first Development]**   | Define YAML schemas before resolvers to enforce contracts.                | Collaborative teams.                     |

---

## **Best Practices**
1. **Modularity**:
   - Split schemas by domain (e.g., `types/auth.yaml`, `queries/search.yaml`).
   - Use imports (if supported by your toolchain).
   ```yaml
   # _extends: base.yml
   # (Hypothetical; check tool capabilities.)
   ```

2. **Validation**:
   - Run `graphql-yaml --validate` in CI.
   - Use `no-unsafe-resolver-reference` linters.

3. **Documentation**:
   - Add `description` fields to all types/queries.
   - Link YAML files to downstream tools (e.g., Swagger for OpenAPI).

4. **Performance**:
   - Cache generated SDL to avoid repeated YAML→GraphQL conversions.

5. **Security**:
   - Validate resolver paths in CI to prevent runtime errors.
   - Use YAML anchors for reusable directives.

---

## **Troubleshooting**
| Issue                          | Solution                                  |
|--------------------------------|-------------------------------------------|
| Resolver not found             | Check path syntax (e.g., `resolvers/user.js#getUser`). |
| Circular dependencies          | Split schemas into smaller modules.       |
| YAML syntax errors             | Run `yamllint` or VS Code YAML extension. |
| Schema conflicts               | Use unique type names across files.       |

---

## **Tools & Libraries**
| Tool/Library                  | Purpose                                      | Link                                  |
|-------------------------------|---------------------------------------------|---------------------------------------|
| `graphql-yaml`                | Convert YAML to GraphQL SDL.                | [npm](https://www.npmjs.com/package/graphql-yaml) |
| `js-yaml`                     | Parse YAML in Node.js.                      | [npm](https://www.npmjs.com/package/js-yaml) |
| `yamllint`                    | Lint YAML files.                            | [GitHub](https://github.com/adrienverge/yamllint) |
| `graphql-codegen`             | Generate types/clients from YAML schemas.   | [GitHub](https://github.com/dotansimha/graphql-code-generator) |
| Apollo Server                 | Integrate YAML schemas with Apollo.        | [Docs](https://www.apollographql.com/docs/apollo-server/) |

---
**Note:** For production use, combine YAML authoring with a **schema registry** (e.g., GraphQL Codegen) to auto-generate clients and enforce consistency.