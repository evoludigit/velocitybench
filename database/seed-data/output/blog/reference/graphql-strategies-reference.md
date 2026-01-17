# **[Pattern] GraphQL Strategies Reference Guide**

---

## **Overview**
The **GraphQL Strategies** pattern provides a structured way to implement flexible query resolution in GraphQL APIs. Unlike traditional REST endpoints, GraphQL allows clients to request only the data they need, but this flexibility requires careful strategy design to optimize performance, caching, and data fetching complexity. This pattern defines reusable strategies for common GraphQL use cases, ensuring consistency in query execution, mutation handling, and pagination.

Strategies in GraphQL can be categorized into:
- **Fetching Strategies** (for queries): How data is retrieved from one or more sources.
- **Mutation Strategies** (for mutations): How data is validated, transformed, and persisted.
- **Aggregation Strategies** (for computed fields): How derived data (e.g., counts, averages) is calculated.

This guide covers core strategies, schema design considerations, and practical implementation examples.

---

## **Key Concepts**

### **1. Strategy Hierarchy**
Strategies are organized into types:

| **Strategy Type**       | **Purpose**                                                                                     | **Use Case Examples**                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Fetch**               | Defines how to retrieve data (direct DB query, cache lookup, or resolver chain).                | User profiles, blog posts, nested relationships.                                     |
| **Mutation**            | Handles input validation, business logic, and persistence (e.g., database, external API).      | User registration, order creation, payment processing.                               |
| **Aggregation**         | Computes derived fields (e.g., statistics, summarized data) without fetching raw records.     | Product sales trends, user activity analytics.                                       |
| **Pagination**          | Manages large datasets with cursor-based or offset-based pagination.                           | Infinite scroll feeds, admin dashboards.                                            |

---

### **2. Core Principles**
- **Decoupled Resolvers**: Each strategy encapsulates a single responsibility (e.g., fetching a user’s posts).
- **Reusability**: Strategies can be shared across multiple resolvers or mutated.
- **Extensibility**: New strategies can be added without modifying existing code.
- **Performance**: Strategies include caching, batching, and data loading optimizations.

---

## **Schema Reference**

### **1. Fetch Strategy Schema**
| **Field**          | **Type**               | **Description**                                                                                     | **Strategy Example**                     |
|---------------------|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------|
| `user(id: ID!)`     | `UserType!`            | Fetches a single user by ID, combining database query + cache.                                  | `FetchUserById`                           |
| `posts(limit: Int)` | `[PostType!]!`         | Returns paginated posts via cursor-based pagination.                                              | `FetchPostsWithCursor`                   |
| `recentActivity`    | `ActivitySummary`      | Aggregates recent user activities (computed field).                                               | `AggregateRecentActivity`                |

---

### **2. Mutation Strategy Schema**
| **Field**          | **Type**               | **Input Type**       | **Description**                                                                                     | **Strategy Example**                     |
|---------------------|------------------------|----------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------|
| `createPost`        | `PostType!`            | `PostInput`          | Validates input, processes media uploads, and persists to DB.                                       | `PersistPostWithValidation`              |
| `updateProfile`     | `UserType!`            | `ProfileUpdateInput` | Applies business rules (e.g., password hashing) before DB update.                                | `UpdateProfileWithAuditLog`              |

---

### **3. Aggregation Strategy Schema**
| **Field**          | **Type**               | **Description**                                                                                     | **Strategy Example**                     |
|---------------------|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------|
| `stats`             | `PostStats`            | Computes total posts, top categories, and monthly trends without fetching individual posts.        | `ComputePostStatsWithDBViews`            |
| `recommendations`   | `[PostType!]`          | Uses ML or collaborative filtering to suggest posts (cached for performance).                     | `GenerateRecommendations`                |

---

## **Implementation Details**

### **1. Fetch Strategies**
#### **a. Single-Entity Fetch (`FetchUserById`)**
- **Purpose**: Retrieve a user with nested data (e.g., posts, orders).
- **Implementation**:
  ```graphql
  type User {
    id: ID!
    name: String!
    posts: [Post!]! @fetchUserPosts
  }
  ```
  - **Resolver**:
    ```javascript
    async fetchUserPosts(parent, args, { dataSources }) {
      const user = await dataSources.db.getUser(parent.id);
      return dataSources.db.getPostsByUser(user.id); // Batch load
    }
    ```

#### **b. Paginated Fetch (`FetchPostsWithCursor`)**
- **Purpose**: Efficiently fetch posts with cursor-based pagination.
- **Schema**:
  ```graphql
  type Query {
    posts(cursor: String, limit: Int = 10): PaginatedPosts!
  }

  type PaginatedPosts {
    items: [Post!]!
    nextCursor: String
  }
  ```
  - **Resolver**:
    ```javascript
    async fetchPosts(root, { cursor, limit }, { db }) {
      const posts = await db.getPaginatedPosts(cursor, limit);
      return {
        items: posts.items,
        nextCursor: posts.nextCursor,
      };
    }
    ```

---

### **2. Mutation Strategies**
#### **a. Input Validation (`PersistPostWithValidation`)**
- **Purpose**: Validate and sanitize input before persisting.
- **Schema**:
  ```graphql
  input PostInput {
    title: String!
    content: String!
    tags: [String!]
  }

  type Mutation {
    createPost(input: PostInput!): Post!
  }
  ```
  - **Resolver**:
    ```javascript
    async createPost(_, { input }, { db, validators }) {
      const sanitizedInput = validators.sanitize(input);
      const post = await db.createPost(sanitizedInput);
      return post;
    }
    ```

#### **b. Transactional Mutations (`UpdateProfileWithAuditLog`)**
- **Purpose**: Ensure atomicity in multi-step mutations (e.g., profile update + audit log).
- **Resolver**:
  ```javascript
  async updateProfile(_, { input }, { db, auditLogger }) {
    await db.transaction(async (tx) => {
      const updatedUser = await tx.updateUser(input);
      await auditLogger.log('profile_update', updatedUser);
    });
    return updatedUser;
  }
  ```

---

### **3. Aggregation Strategies**
#### **a. Computed Fields (`ComputePostStatsWithDBViews`)**
- **Purpose**: Avoid fetching raw data for derived metrics.
- **Schema**:
  ```graphql
  type PostStats {
    totalPosts: Int!
    monthlyTrends: [MonthlyTrend!]!
  }
  ```
  - **Resolver**:
    ```javascript
    async computePostStats(_, __, { db }) {
      return {
        totalPosts: await db.getTotalPosts(),
        monthlyTrends: await db.getMonthlyTrends(), // Materialized view
      };
    }
    ```

#### **b. Cached Aggregations (`GenerateRecommendations`)**
- **Purpose**: Serve personalized recommendations with low latency.
- **Schema**:
  ```graphql
  type Recommendation {
    id: ID!
    title: String!
    relevanceScore: Float!
  }

  type Query {
    recommendations(userId: ID!): [Recommendation!]!
  }
  ```
  - **Resolver**:
    ```javascript
    async recommendations(_, { userId }, { cache, recommender }) {
      const key = `recs:${userId}`;
      let recs = cache.get(key);
      if (!recs) {
        recs = await recommender.generate(userId);
        cache.set(key, recs, 3600); // Cache for 1 hour
      }
      return recs;
    }
    ```

---

## **Query Examples**

### **1. Fetching Data**
```graphql
# Fetch a user with posts (using FetchUserById)
query {
  user(id: "123") {
    name
    posts {
      title
      publishedAt
    }
  }
}
```

```graphql
# Paginated posts (using FetchPostsWithCursor)
query {
  posts(cursor: "abc123", limit: 5) {
    items {
      title
      author { name }
    }
    nextCursor
  }
}
```

---

### **2. Mutations**
```graphql
# Create a post (using PersistPostWithValidation)
mutation {
  createPost(input: {
    title: "GraphQL Best Practices",
    content: "Learn how to optimize...",
    tags: ["graphql", "performance"]
  }) {
    id
    title
  }
}
```

```graphql
# Update profile with audit log (using UpdateProfileWithAuditLog)
mutation {
  updateProfile(input: {
    displayName: "New Name",
    bio: "Updated bio..."
  }) {
    id
    displayName
  }
}
```

---

### **3. Aggregations**
```graphql
# Get post stats (using ComputePostStatsWithDBViews)
query {
  stats {
    totalPosts
    monthlyTrends {
      month
      count
    }
  }
}
```

```graphql
# Get recommendations (using GenerateRecommendations)
query {
  recommendations(userId: "456") {
    id
    title
    relevanceScore
  }
}
```

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                                       | **When to Use**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **DataLoader**                   | Batched and cached loading of related data to reduce N+1 queries.                                    | Fetching nested data (e.g., users with posts).                               |
| **Schema Stitching**             | Combines multiple GraphQL schemas (e.g., microservices) into a unified API.                         | Federated architectures with disparate data sources.                          |
| **Persistent Queries**          | Predefined GraphQL queries cached and served via unique IDs to reduce bandwidth.                     | High-frequency queries (e.g., analytics dashboards).                         |
| **Polymorphic Types**            | Handles multiple data types under a single GraphQL type (e.g., `Media` with images/videos).       | APIs serving diverse media types.                                             |
| **Directives**                   | Custom directives (e.g., `@auth`, `@cacheControl`) to modify resolver behavior.                    | Fine-grained control over query execution (e.g., role-based access).         |
| **Apollo Federation**            | Extends schema stitching with shared types and subgraphs for microservices.                        | Large-scale GraphQL implementations.                                          |

---

## **Best Practices**
1. **Reuse Strategies**: Define strategies once (e.g., `FetchUserById`) and reuse across multiple resolvers.
2. **Leverage Caching**: Cache aggregations and recommendations to reduce compute load.
3. **Optimize Pagination**: Prefer cursor-based pagination over offset-based for large datasets.
4. **Validate Early**: Use input validation strategies (e.g., in mutations) to fail fast.
5. **Monitor Performance**: Track resolver execution time and query depth to identify bottlenecks.
6. **Document Strategies**: Clearly label strategies in your schema with comments or directives (e.g., `@fetchStrategy`).