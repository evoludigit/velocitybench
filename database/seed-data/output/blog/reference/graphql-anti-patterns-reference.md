# **[Pattern] GraphQL Anti-Patterns Reference Guide**

## **Overview**
GraphQL is a powerful query language for APIs, but poor design decisions—for example, overcomplicating schemas, ignoring performance, or violating best practices—can lead to **anti-patterns**. These patterns degrade developer experience, increase complexity, and harm maintainability. This guide outlines common GraphQL anti-patterns, their implications, and best practices to avoid them.

---

## **Schema Reference (Anti-Patterns & Fallbacks)**

| **Anti-Pattern**               | **Description**                                                                                     | **Avoid By Doing Instead**                                                                                     |
|---------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Over-fetching**               | Clients receive unnecessary fields, increasing payload size.                                        | Use **field-level pagination** (`limit`, `offset`) or **cursor-based pagination**.                          |
| **Under-fetching**              | Clients must query multiple times to get all required data due to missing nested fields.            | Use **auto-resolving nested fields** where possible or **data loading libraries** (e.g., DataLoader).         |
| **Monolithic Queries**          | Single queries return massive amounts of data, causing performance bottlenecks.                    | Split into **smaller operations** (mutations, subscriptions) or **batch requests**.                          |
| **Deep Nesting**                | Nested relations cause exponential query complexity.                                                  | Limit nesting depth (e.g., use **graph-like structure** instead of deep trees).                               |
| **Unused Resolvers**            | Resolvers exist but are never invoked due to unused fields.                                           | Remove unused fields and clean up schema periodically.                                                      |
| **Overly Complex Types**        | Schema types become bloated with too many fields, making them harder to reason about.                 | **Split into smaller, focused types** (e.g., `User`, `UserProfile` instead of a single `User` with 100 fields).|
| **Missing Input Validation**    | Input mutations lack validation, leading to unintended state changes.                                | Use **GraphQL Input Types** with `@validate` or libraries like **GraphQL Shield**.                           |
| **No Error Handling**           | Errors are returned in raw format without context.                                                   | Implement **custom error types** (e.g., `UserError`, `ValidationError`) and **error codes**.                 |
| **Ignoring Persistence**        | Schema doesn’t align with database schema, causing inefficient queries.                            | Use **graph-relational mapping** (e.g., **Prisma**, **TypeORM**) to optimize queries.                      |
| **Hardcoded Query Depth Limit** | Arbitrary GraphQL depth limits lead to inconsistent behavior.                                       | Set **dynamic depth limits** based on use case or use **execution policies**.                                |
| **Exposing Sensitive Data**     | Fields containing PII or secrets are queryable by default.                                           | Use **field-level authorization** (e.g., `@auth`, **GraphQL Shield**) or restrict with **directives**.         |
| **No Versioning**               | Schema changes break existing queries without backward compatibility.                                | Use **schema evolution strategies** (e.g., **deprecation warnings**, **federation**).                       |

---

## **Query Examples: Anti-Patterns vs. Best Practices**

### **Anti-Pattern 1: Over-Fetching**
**❌ Bad (Unnecessary Data Transfer)**
```graphql
query {
  user(id: "1") {
    id
    name
    email
    posts {
      id
      title
      content
      comments {
        id
        text
        author {
          id
          name
        }
      }
    }
  }
}
```
**✅ Better (Field Pagination)**
```graphql
query {
  user(id: "1") {
    id
    name
    email
    posts(limit: 10, first: 5) {
      id
      title
    }
  }
}
```

### **Anti-Pattern 2: Deep Nesting**
**❌ Bad (N+1 Query Problem)**
```graphql
query {
  post(id: "1") {
    id
    author {
      id
      name
      posts {
        id
        title
      }
    }
  }
}
```
**✅ Better (Denormalized Data or Batch Fetching)**
```graphql
query {
  post(id: "1") {
    id
    author {
      id
      name
    }
  }
}
```
*(Resolve `posts` separately or use **DataLoader** to batch author data.)*

### **Anti-Pattern 3: Missing Input Validation**
**❌ Bad (No Validation)**
```graphql
mutation {
  updateUser(id: "1", name: "") {
    id
    name
  }
}
```
**✅ Better (Input Type with Validation)**
```graphql
input UserInput {
  name: String! @validate(length: { min: 1 })
}

mutation UpdateUser($input: UserInput!) {
  updateUser(input: $input) {
    id
    name
  }
}
```

### **Anti-Pattern 4: Unauthorized Data Exposure**
**❌ Bad (Unrestricted Field Access)**
```graphql
type User {
  id: ID!
  name: String!
  creditCard: String!  # Unintended exposure
}
```
**✅ Better (Field-Level Permissions)**
```graphql
type User {
  id: ID!
  name: String!
  creditCard: String! @auth(requires: ADMIN)
}
```

---

## **Implementation Details: Key Concepts**

### **1. Performance Optimization**
- **Batch & Persist Data**: Use **DataLoader** to avoid N+1 queries.
- **Fragment Usage**: Reuse query fragments to reduce redundancy.
- **Pagination**: Implement **cursor-based pagination** for large datasets.

### **2. Schema Design Best Practices**
- **Keep Types Small**: Avoid monolithic types; split by domain (e.g., `User`, `Order`).
- **Use Interfaces/Unions**: For polymorphic data (e.g., `Content` interface for `Post`/`Comment`).
- **Deprecate Carefully**: Use `@deprecated` with a migration path.

### **3. Security Considerations**
- **Field-Level Authorization**: Restrict sensitive fields (e.g., `@auth`).
- **Rate Limiting**: Protect against excessive queries.
- **Input Sanitization**: Validate all mutations (e.g., `@validate`).

### **4. Tooling & Libraries**
| Tool/Library          | Purpose                                                                 |
|-----------------------|-------------------------------------------------------------------------|
| **GraphQL Shield**    | Query depth limits, permissions, rate limiting.                         |
| **Prisma**            | ORM for efficient schema-to-database mapping.                          |
| **Relay JS**          | Caching strategies for large datasets.                                 |
| **GraphQL Playground**| Schema exploration & testing.                                          |
| **Apollo Federation** | Microservices-compatible schema composition.                           |

---

## **Related Patterns**

| **Related Pattern**          | **Description**                                                                                     | **When to Use**                                                                 |
|-------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[GraphQL Federation]**      | Splits microservices into a scalable, modular schema.                                             | When building microservices with independent schemas.                          |
| **[Relay Modern]**            | Optimizes client-side caching and queries.                                                        | Frontend-heavy apps with large datasets.                                       |
| **[Persistent Queries]**     | Pre-registers queries to avoid mutation overhead.                                                 | Highly dynamic client apps with frequent queries.                              |
| **[GraphQL Subscriptions]**   | Real-time updates via WebSockets.                                                                | Apps needing push notifications (e.g., chat, live data).                        |
| **[GraphQL Batch Loading]**   | Reduces database queries via batching.                                                            | When resolving deeply nested relations.                                        |

---

## **Conclusion**
Avoiding GraphQL anti-patterns ensures **scalability, security, and maintainability**. Focus on:
✅ **Efficient data fetching** (pagination, batching)
✅ **Clean schema design** (modular types, validation)
✅ **Security-first approach** (authorization, input sanitization)

By following these guidelines, you’ll build **robust, high-performance GraphQL APIs** that adapt to future needs.