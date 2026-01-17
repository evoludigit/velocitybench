```markdown
# Pre-Compiled Query Plans: Compiling GraphQL into SQL at Schema Time

**Faster queries. Predictable performance. Less runtime overhead.**

Most GraphQL implementations today compile queries *at runtime*—meaning every time a query executes, the server must:
1. Parse the GraphQL AST,
2. Validate it against the schema,
3. Generate an execution plan,
4. Optimize it,
5. Execute it.

This runtime compilation adds noticeable latency—especially for APIs under heavy load where queries vary or get cached poorly. It also introduces unpredictability: a "simple" query might hit a slow path due to runtime optimizations.

**What if we could compile GraphQL into optimized SQL *once*, at schema definition time?** That’s the promise of the **Pre-Compiled Query Plans** pattern—used by tools like FraiseQL to generate reusable, high-performance SQL plans that skip the runtime parsing and optimization step entirely.

In this post, we’ll explore:
- Why runtime query planning is a performance bottleneck
- How pre-compiled query plans work under the hood
- Practical examples with SQL and GraphQL
- Tradeoffs and when to consider this approach
- Lessons from production deployments

---

## The Problem: Runtime Query Planning is a Latency Tax

Before diving into the solution, let’s quantify the problem. Consider this common scenario:

```graphql
# A typical GraphQL query to fetch a product with its reviews
query ProductWithReviews($productId: ID!) {
  product(id: $productId) {
    id
    name
    price
    reviews {
      rating
      comment
      author {
        name
      }
    }
  }
}
```

Under traditional GraphQL execution:
1. **Parsing**: The query string is parsed into an Abstract Syntax Tree (AST) (e.g., `@graphql/middlewares` or `graphql-js`).
2. **Validation**: The AST is validated against your schema (e.g., does `product.reviews` exist?).
3. **Execution Plan Generation**: The resolver picker determines which resolvers to call (e.g., `ProductResolver`, then `ReviewsResolver`).
4. **Runtime Query Optimization**: The query executor optimizes based on context (e.g., filter known redundant fields).

Each step adds milliseconds—especially if:
- The query changes dynamically (e.g., client-side toggles).
- The schema is large with many nested types.
- You’re using a complex ORM (e.g., with `select *` or unhelpful eager-loading).

Example overheads:
- **Runtime compilation alone** can add **5–20ms** per query (depending on server load).
- If you cache the query string but not the parsed AST, this cost repeats for identical queries.
- Under high load, this overhead compounds, making it harder to guarantee SLAs.

---

## The Solution: Pre-Compile GraphQL into SQL Plans

The **Pre-Compiled Query Plans** pattern takes a radical step: **compile queries into SQL at schema definition time** rather than execution time. Here’s how it works:

### Core Idea
1. **Schema-Level Compilation**: During application startup, FraiseQL inspects your GraphQL schema and generates **SQL execution plans** for every possible query defined in your schema.
2. **Reusable Plans**: These plans are stored in memory (or a simple cache) and reused for every identical query.
3. **Direct SQL Execution**: When a GraphQL query runs, the server checks its cache for a pre-compiled plan, executes it directly, and returns the result.

This eliminates:
- The runtime parsing step.
- The resolver picker overhead.
- Some query optimization logic (since plans are baked in).

---

## How FraiseQL Implements Pre-Compiled Plans

FraiseQL’s approach is inspired by tools like **Dolt** (a SQL database optimized for versioning) and **Gremlon** (a GraphQL-to-SQL compiler). Here’s how it works in practice:

### 1. Schema Definition → SQL Plans
When you define your schema, FraiseQL generates SQL plans for *all* queries that resolve to your types. For example:

```graphql
# Schema definition
type Product {
  id: ID!
  name: String!
  price: Float!
  reviews: [Review!]!
}

type Review {
  rating: Int!
  comment: String!
  author: User!
}

type User {
  name: String!
}
```

FraiseQL might generate this SQL plan for the query from earlier:

```sql
-- Pre-compiled plan for ProductWithReviews
SELECT
  p.id AS "product.id",
  p.name AS "product.name",
  p.price AS "product.price",
  r.rating AS "product.reviews->[].rating",
  r.comment AS "product.reviews->[].comment",
  u.name AS "product.reviews->[].author.name"
FROM
  products p
LEFT JOIN reviews r ON p.id = r.product_id
LEFT JOIN users u ON r.author_id = u.id
;
```

### 2. Query Execution via Plan
At runtime, instead of parsing the GraphQL query, FraiseQL:
1. Matches the incoming query to its pre-compiled plan.
2. Binds variables (e.g., `$productId`).
3. Executes the SQL directly.

Example with a variable:
```sql
-- Dynamic execution with bound variable
SELECT ... WHERE p.id = $productId
```

This skips the entire GraphQL AST generation step.

---

## Implementation Guide: Adding Pre-Compiled Plans to Your Stack

Let’s walk through a step-by-step implementation using FraiseQL (hypothetical—adapted for educational purposes).

### Step 1: Define Your Schema
Start with a GraphQL schema (e.g., using `graphql-js`):

```javascript
// schema.js
const { buildSchema } = require('graphql');

const schema = buildSchema(`
  type Product {
    id: ID!
    name: String!
    price: Float!
    reviews: [Review!]!
  }

  type Review {
    rating: Int!
    comment: String!
    author: User!
  }

  type User {
    name: String!
  }

  type Query {
    product(id: ID!): Product!
    products: [Product!]!
  }
`);
```

### Step 2: Configure FraiseQL
Install FraiseQL and hook it into your server:

```bash
npm install fraiseql
```

```javascript
// server.js
const express = require('express');
const { FraiseQLServer } = require('fraiseql');
const { schema } = require('./schema');

const app = express();
const fraiseql = new FraiseQLServer({
  schema,
  database: 'postgres://user:pass@localhost/db',
});

// Compile schema at startup
fraiseql.compileSchema();

// Attach GraphQL endpoint
app.use('/graphql', fraiseql.middleware());
```

### Step 3: Write Optimized Resolvers
FraiseQL handles the SQL generation, but you still need mock or real data access. Here’s a mock resolver setup:

```javascript
// resolvers.js
const resolvers = {
  Query: {
    product: (_, { id }) => {
      // FraiseQL will handle the SQL; this just mocks data
      return {
        id,
        name: 'Premium Widget',
        price: 49.99,
        reviews: [
          { rating: 5, comment: 'Love it!', author: { name: 'Alice' } }
        ]
      };
    }
  }
};
```

### Step 4: Enable Plan Caching
FraiseQL caches compiled plans by default. To inspect them:

```javascript
// Debugging: Log compiled plans
fraiseql.on('compiledPlan', (plan) => {
  console.log('Compiled plan:', plan.sql);
});
```

### Step 5: Test Query Execution
Send a query to your server:

```javascript
const query = `
  query ProductWithReviews($productId: ID!) {
    product(id: $productId) {
      name
      price
      reviews { rating }
    }
  }
`;

const variables = { productId: '123' };

// FraiseQL executes the pre-compiled plan directly
const response = await fraiseql.execute(query, variables);
console.log(response);
```

---

## Common Mistakes to Avoid

1. **Assuming “Compiler” = No Runtime Flexibility**
   - Pre-compiled plans *are* rigid: they don’t adapt to schema changes at runtime.
   - **Fix**: Use feature flags to swap schemas during deployment.

2. **Over-Compiling for Dynamic Queries**
   - If your clients frequently send ad-hoc GraphQL queries, pre-compiling may not help.
   - **Fix**: Only compile queries for known, high-volume endpoints.

3. **Ignoring SQL Optimization**
   - FraiseQL compiles to SQL, but bad SQL is still bad SQL.
   - **Fix**: Inspect the generated plans and tweak your schema (e.g., avoid nested `IN` clauses).

4. **Forgetting Edge Cases**
   - Some GraphQL features (e.g., subscriptions, mutations) may not map neatly to pre-compiled plans.
   - **Fix**: Validate against a subset of your schema first.

5. **Over-Caching Plans**
   - Storing thousands of plans in memory can consume memory.
   - **Fix**: Cache only the most critical queries and fall back to runtime compilation for others.

---

## Key Takeaways

✅ **Performance Wins**:
- Eliminates runtime query parsing/optimization (5–20ms saved per query).
- Predictable latency for known queries.

✅ **When to Use**:
- High-traffic APIs with stable schemas.
- Queries that are frequently repeated (e.g., client-side caching).
- Teams prioritizing consistency over flexibility.

⚠️ **Tradeoffs**:
- **Less Flexibility**: Can’t handle arbitrary GraphQL queries dynamically.
- **Cold Start**: First request after a schema change may be slow.
- **Complexity**: Requires careful schema design.

🔧 **Tools to Explore**:
- FraiseQL (pre-compiled GraphQL → SQL).
- Gremlon (GraphQL-to-SQL compiler).
- Apollo Federation (for distributed schemas).

---

## Conclusion: When to Pre-Compile, When Not To

Pre-compiled query plans are a powerful tool for APIs where:
- Performance is critical (e.g., high-traffic dashboards).
- Queries are predictable (e.g., client-side cached requests).
- Your team prefers compile-time guarantees over runtime adaptability.

However, if your API:
- Handles ad-hoc queries (e.g., a developer console).
- Requires complex dynamic filtering.
- Needs real-time schema updates,

then traditional runtime compilation might be a safer choice.

**Final Advice**: Start with a pilot. Compile only the most important queries, measure the impact, and gradually expand. As you refine your schema, you’ll uncover more opportunities to optimize further.

---
**What’s Your Approach?**
Are you using pre-compiled plans in production? Share your experiences (or struggles!) in the comments. Or better yet: try FraiseQL and let us know how it works for your stack!

---
**Further Reading**:
- [FraiseQL Documentation](https://fraiseql.com/docs) (hypothetical)
- [GraphQL Performance Pitfalls](https://www.apollographql.com/blog/graphql-performance-pitfalls/)
- [Why Compiled Languages Are Faster](https://blog.filippo.io/compiled-vs-interpreted-languages/)
```