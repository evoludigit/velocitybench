# **[Pattern] GraphQL Conventions – Reference Guide**

## **Overview**
GraphQL Conventions define a structured approach to designing schemas, queries, and mutations that ensure consistency, scalability, and developer-friendly interactions. Unlike REST, GraphQL’s flexibility can lead to inconsistencies if not guided by explicit conventions. This pattern establishes best practices for **naming conventions, schema design, query structure, and error handling**, ensuring maintainable and predictable API behavior.

This guide covers:
- Core conventions for schema design (types, fields, arguments)
- Query and mutation patterns (best practices, pagination, filtering)
- Error handling and data validation
- Integration with backend systems (database, microservices)
- Example implementations in GraphQL Schema Definition Language (SDL) and resolver logic.

---

## **Schema Reference**

| **Category**       | **Convention**                          | **Example**                                                                 | **Purpose**                                                                 |
|--------------------|-----------------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Type Naming**    | **PascalCase** (Singular nouns)         | `User`, `ProductCategory`                                                  | Clear, human-readable type names.                                           |
| **Field Naming**   | **camelCase**                           | `getUserEmail`, `isActive`                                                  | Follows JavaScript/TypeScript conventions for consistency.                |
| **Argument Naming**| **camelCase**                           | `filter`, `limit`, `after`                                                  | Matches query arguments to natural language usage.                         |
| **Enum Values**    | **UPPER_SNAKE_CASE**                    | `STATUS_ACTIVE`, `ROLE_ADMIN`                                               | Standardized for constants.                                                 |
| **Input Types**    | **PascalCase + "Input"**                | `UserInput`, `ProductFilterInput`                                           | Distinguish from regular objects.                                           |
| **Pagination**     | **Cursor-based or Offset-based**        | `first`, `after` (cursor), `offset`, `limit`                                 | Avoids N+1 queries and ensures scalability.                                  |
| **Filtering**      | **Input Object for Complex Filters**     | `{ status: [USER_STATUS], createdAt: { gt: "2023-01-01" } }`               | Enables flexible, nested filtering.                                         |
| **Relationships**  | **Use `@arg` for Resolvers (if needed)** | `user: User! @args(query: String!)`                                        | Explicitly define resolver dependencies.                                     |
| **Default Values** | **Explicit `default` in SDL**           | `default: true` in `User { isActive: Boolean! @default(value: true) }`    | Avoids runtime assumptions.                                                  |
| **Description**    | **SDL Comments for Clarity**            | `""" Returns the user with the given ID or throws an error. """`           | Improves IDE tooling and documentation.                                      |
| **Error Messages** | **Standardized Error Types**            | `error "Not found" { code: "USER_NOT_FOUND" }`                             | Consistent error handling across the API.                                   |

---

## **Query Examples**

### **1. Basic Query (Single Resource)**
**Request:**
```graphql
query {
  user(id: "123") {
    id
    name
    email
    status
  }
}
```
**Response:**
```json
{
  "data": {
    "user": {
      "id": "123",
      "name": "Alice",
      "email": "alice@example.com",
      "status": "ACTIVE"
    }
  }
}
```

### **2. Paginated Query (Cursor-Based)**
**Request:**
```graphql
query {
  products(filter: { category: "ELECTRONICS" }, first: 10, after: "cursor123") {
    edges {
      node {
        id
        name
        price
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```
**Response:**
```json
{
  "data": {
    "products": {
      "edges": [
        { "node": { "id": "1", "name": "Laptop", "price": 999 }, "cursor": "cursor456" },
        { "node": { "id": "2", "name": "Phone", "price": 699 }, "cursor": "cursor789" }
      ],
      "pageInfo": { "hasNextPage": true, "endCursor": "cursor789" }
    }
  }
}
```

### **3. Filtered Query (Nested Input)**
**Request:**
```graphql
query {
  orders(
    filter: {
      status: [ORDER status: DELIVERED]
      createdAt: { gt: "2023-01-01" }
    }
  ) {
    id
    amount
    customer {
      name
    }
  }
}
```

### **4. Mutation with Input Object**
**Request:**
```graphql
mutation {
  updateUser(input: {
    id: "123"
    update: {
      name: "Alice Smith"
      email: "new@example.com"
    }
  }) {
    user {
      id
      name
    }
    errors {
      field
      message
    }
  }
}
```
**Response:**
```json
{
  "data": {
    "updateUser": {
      "user": { "id": "123", "name": "Alice Smith" },
      "errors": []
    }
  }
}
```

### **5. Subscription (Real-Time Updates)**
**Request:**
```graphql
subscription {
  onUserUpdated {
    user {
      id
      name
    }
    timestamp
  }
}
```
**Response (Streaming):**
```json
{
  "data": {
    "onUserUpdated": {
      "user": { "id": "123", "name": "Alice Updated" },
      "timestamp": "2023-10-15T12:00:00Z"
    }
  }
}
```

---

## **Implementation Details**

### **1. Schema Design Principles**
- **Avoid Over-Fetching/Under-Fetching**: Design fields to be reusable (e.g., `User` includes `id`, `name`, `email`).
- **Leverage Interfaces**: Define shared fields (e.g., `Node` interface for all queryable types).
- **Use Unions for Ambiguous Types**: e.g., `SearchResult` that can be `User | Product`.

**Example SDL:**
```graphql
interface Node {
  id: ID!
}

type User implements Node {
  id: ID!
  name: String!
  email: String!
}

type Product implements Node {
  id: ID!
  name: String!
  price: Float!
}

union SearchResult = User | Product
```

### **2. Query Complexity Analysis**
- **Use `@complexity` Directives** (e.g., Apollo’s `graphql-complexity`):
  ```graphql
  type Query {
    search(query: String!): [SearchResult] @complexity(10)
  }
  ```
- **Rate-Limit Complex Queries**: Reject requests exceeding a threshold (e.g., 1,000 units).

### **3. DataLoader for Batch Loading**
- **Resolve N+1 Queries**: Use `dataloader` to fetch related data in batches.
  ```javascript
  const dataLoader = new DataLoader(async (userIds) => {
    const users = await db.query('SELECT * FROM users WHERE id IN ($1)', userIds);
    return userIds.map(id => users.find(u => u.id === id));
  });

  UserType.resolveField('orders', (parent, args) => {
    return dataLoader.load(parent.id);
  });
  ```

### **4. Error Handling**
- **Standardized Errors**: Use `graphql-error-formatter` or custom scalars (e.g., `Error!`).
  ```graphql
  scalar Error

  type Mutation {
    createUser(input: UserInput!): User @returns [Error!]
  }
  ```
- **Resolver Error Handling**:
  ```javascript
  resolve: async (parent, args) => {
    try {
      return await userService.create(args.input);
    } catch (error) {
      throw new Error(`CREATE_USER_FAILED: ${error.message}`);
    }
  }
  ```

### **5. Testing**
- **Schema Validation**: Use `graphql-tools` to validate SDL against conventions:
  ```javascript
  const schema = makeExecutableSchema({
    typeDefs: [schemaSDL],
    resolvers: resolvers,
    validate: (schema) => [
      validateNoDeprecatedFields(),
      validateNoUnusedFragments(),
    ],
  });
  ```
- **Query Testing**: Use `graphql-request` for unit tests:
  ```javascript
  const response = await request(
    schemaEndpoint,
    `
      query {
        user(id: "123") { name }
      }
    `
  );
  expect(response.data.user.name).toBe("Alice");
  ```

---

## **Tools & Integrations**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **GraphQL Code Generator** | Auto-generates TypeScript/Java clients from SDL.                            |
| **Apollo Studio**      | Schema registry, performance insights, and monitoring.                     |
| **Hasura**             | Auto-generates GraphQL from databases with conventions.                     |
| **Prisma**             | ORM with GraphQL support (convention-based schema generation).               |
| **GraphQL Playground** | Interactive IDE for testing queries.                                       |
| **Stitch**             | Federates microservices with GraphQL conventions.                           |

---

## **Related Patterns**
1. **[Schema Stitching](https://www.apollographql.com/docs/stitching/)**
   - Combine multiple GraphQL schemas into a unified API while preserving conventions.
2. **[Data Federation](https://graphql.org/docs/guides/data-fetching/#data-federation/)**
   - Distribute resolvers across services while maintaining consistent field naming.
3. **[Subscriptions with Pub/Sub](https://www.apollographql.com/docs/apollo-server/data/subscriptions/)**
   - Real-time updates aligned with GraphQL conventions for event-driven systems.
4. **[Schema Evolution](https://www.graphql-code-generator.com/schema-evolution/)**
   - Safely modify schemas while respecting backward compatibility.
5. **[Query Depth Limiting](https://www.apollographql.com/docs/apollo-server/data/max-depth/)**
   - Prevent overly complex queries (complements complexity analysis).

---

## **Best Practices Summary**
| **Area**               | **Best Practice**                                                                 |
|------------------------|-----------------------------------------------------------------------------------|
| **Naming**             | Consistently use `PascalCase` for types, `camelCase` for fields/args.            |
| **Pagination**         | Prefer cursor-based over offset-based for scalability.                            |
| **Error Handling**     | Standardize error types and messages for maintainability.                          |
| **Performance**        | Use `DataLoader` to batch resolve related data and analyze query complexity.     |
| **Testing**            | Validate SDL and test queries against the schema.                                 |
| **Tooling**            | Leverage generators (e.g., GraphQL Codegen) and IDEs (e.g., VS Code extensions). |