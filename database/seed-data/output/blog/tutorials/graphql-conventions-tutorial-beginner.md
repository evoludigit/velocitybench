```markdown
---
title: "GraphQL Conventions: Building Maintainable APIs Without Rewriting the Rules"
date: "2023-10-15"
tags: ["GraphQL", "API Design", "Backend Engineering", "Conventions", "Software Patterns"]
description: "Learn how to use GraphQL conventions to create scalable, maintainable APIs that follow best practices out of the box. This guide covers naming conventions, schema design, and practical implementations."
---

# GraphQL Conventions: Building Maintainable APIs Without Rewriting the Rules

GraphQL has revolutionized how we build APIs by giving clients precise control over data fetching. However, as any API grows in complexity, so does the challenge of keeping it **consistent, predictable, and easy to maintain**. Without clear conventions, your GraphQL schema can become a chaotic wildcard—where query names are inconsistent, resolver implementations duplicate logic, and mutations lack clear entry points.

In this guide, we’ll explore **GraphQL conventions**—a set of best practices and design patterns that help you write APIs that are:
✅ **Self-documenting** (clear intents and structure)
✅ **Consistent** (predictable behavior across queries and mutations)
✅ **Scalable** (easy to extend without breaking existing clients)

By following these conventions, you’ll save time debugging, reduce client-side errors, and make your API easier to onboard new developers.

---

## The Problem: Chaos Without Conventions

Imagine you’re joining a project where the GraphQL schema looks like this:

```graphql
query {
  getAuthorDetails(id: "123") {
    name
    postsCount
    books {
      title
      publishedYear
    }
    ...getAuthorProfile # Random fragment
  }
}

mutation {
  updateUserProfile(input: {name: "Alice", email: "alice@example.com"}) {
    success
    user {
      id
      name
    }
    oldEmail
  }
}
```

### **Problems this causes:**
1. **Inconsistent Naming**
   - `getAuthorDetails` vs. `updateUserProfile`; why is `postsCount` not plural?
   - Ambiguous intent ("profile" could mean admin panel or user profile).

2. **Fragment Spraying**
   - Clients inject random fragments (`...getAuthorProfile`) that may not align with your schema’s core queries.

3. **Overly Generic Fields**
   - `success` and `oldEmail` are vague; clients can’t infer how to handle them.

4. **Resolver Duplication**
   - Resolvers might fetch the same author data in multiple places, leading to inconsistencies.

5. **Lack of Error Handling**
   - No standardized way to handle validation errors (e.g., `404 Author not found`).

Without conventions, your API becomes a **moving target**—each new developer rewrites the rules, and clients must adapt to arbitrary schemas. This leads to:
- Higher maintenance costs (fixing broken queries).
- Client-side frustration (guessing field names).
- Security vulnerabilities (exposing unintended fields).

---

## The Solution: GraphQL Conventions

Conventions aren’t mandatory—but they’re the **scaffolding** that prevents your API from becoming a spaghetti monolith. The goal is to enforce **predictability** while keeping the schema flexible.

### Core Principles:
1. **Pluralization for Types** (e.g., `Author`, not `AuthorData`)
2. **Prefixes for Mutations** (e.g., `createAuthor`, `updateAuthor`)
3. **Standardized Field Names** (e.g., `isPublished` instead of `publishedFlag`)
4. **Error Consistency** (always return `{ errors: [String] }` for validation)
5. **Pagination for Lists** (use `first`, `after` for cursor-based pagination)

---

## Components of GraphQL Conventions

### 1. **Naming Conventions**
Consistent naming reduces confusion and makes schema exploration easier.

#### **Type Naming**
Always use **plural nouns** for types to avoid ambiguity:
```graphql
type Author { # Not AuthorData
  id: ID!
  name: String!
  books: [Book]!
}

type Book { # Not BookData
  title: String!
  publishedYear: Int
}
```

#### **Query/Mutation Naming**
Use **verbs for actions**, plural for lists:
```graphql
query {
  authors(limit: 10) { # Lists are plural
    id
    name
  }
}

mutation {
  updateAuthor(id: "123", name: "J.K. Rowling") { # Verb + singular
    author {
      id
      name
    }
  }
}
```

### 2. **Field Naming**
Avoid ambiguity and use **clear, descriptive names**:
| Bad          | Good              | Why?                          |
|--------------|-------------------|-------------------------------|
| `isActive`   | `isPublished`     | More specific to GraphQL      |
| `count`      | `postsCount`      | Explicit type (`Int`) expected |
| `data`       | `authorDetails`   | Avoid generic wrappers         |

### 3. **Pagination**
Use **cursor-based pagination** (recommended) or `limit/offset` (simpler but less efficient):
```graphql
query {
  authors(first: 10, after: "YWRtaW46MTIz") { # First + after cursor
    edges {
      cursor
      node {
        id
        name
      }
    }
    pageInfo {
      hasNextPage
    }
  }
}
```

### 4. **Error Handling**
Standardize error responses to help clients handle failures gracefully:
```graphql
mutation {
  updateAuthor(id: "123", name: "Invalid") {
    author { ... }
    errors # Always include this!
  }
}
```
**Resolver Example (Apollo/TypeGraphQL):**
```typescript
import { Mutation, Resolver, ObjectType, Field } from 'type-graphql';

@ObjectType()
class AuthorError {
  @Field()
  message: string;

  @Field()
  field: string;
}

@ObjectType()
class UpdateAuthorResponse {
  @Field()
  author: Author;

  @Field(() => [AuthorError], { nullable: true })
  errors?: AuthorError[];
}

@Resolver()
export class AuthorResolver {
  @Mutation(() => UpdateAuthorResponse)
  updateAuthor(
    @Arg('id') id: string,
    @Arg('input') input: UpdateAuthorInput
  ): UpdateAuthorResponse {
    const author = getAuthor(id);
    if (!author) {
      return {
        errors: [{ message: 'Author not found', field: 'id' }],
      };
    }
    // Update logic...
    return { author };
  }
}
```

### 5. **Input Types**
Use **input types** for mutations to avoid exposing raw data:
```graphql
input UpdateAuthorInput {
  name: String!
  email: String!
}

mutation {
  updateAuthor(id: "123", input: { name: "Alice" }) {
    author {
      id
      name
    }
  }
}
```

---

## Implementation Guide: Step-by-Step

### Step 1: Define a Schema Convention Document
Create a `SCHEMA_CONVENTIONS.md` file with rules like:
```markdown
## Type Naming
- Always plural (e.g., `Author`, not `AuthorData`).
- Use PascalCase.

## Query/Mutation Naming
- Queries: `getAuthors`, `searchBooks`
- Mutations: `createAuthor`, `deleteBook`

## Field Naming
- Use `isPublished` instead of `isActive`.
- Avoid `data` wrappers.
```

### Step 2: Enforce Conventions with Code
Use **schema stitching** (Apollo) or **TypeScript interfaces** to validate schema generation:
```typescript
// schema.ts
import { buildSchema } from 'type-graphql';

const schema = buildSchema({
  resolvers: [AuthorResolver, BookResolver],
  validate: true, // Enforce TypeGraphQL conventions
});

export default schema;
```

### Step 3: Document Your Schema
Use **GraphQL Playground** or **GraphiQL** to showcase examples:
```graphql
# Example: Fetching authors with pagination
query {
  authors(first: 5) {
    edges {
      node {
        id
        name
      }
    }
    pageInfo {
      hasNextPage
    }
  }
}
```

### Step 4: Client-Side Conventions
Educate your clients to:
- Use **fragments** for reusable data.
- Avoid **over-fetching**.
- Handle errors consistently.

**Example React Hook (Apollo):**
```javascript
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

const GET_AUTHORS = gql`
  query Authors($first: Int!) {
    authors(first: $first) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;

export function AuthorList({ limit = 10 }) {
  const { data, loading, error } = useQuery(GET_AUTHORS, { variables: { first: limit } });
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>{data.authors.edges.map(({ node }) => <div key={node.id}>{node.name}</div>)}</div>;
}
```

---

## Common Mistakes to Avoid

1. **Mixing Snake_Case and CamelCase**
   - Stick to **PascalCase** for types/fields (e.g., `isPublished`, not `is_published`).
   - Clients expect camelCase in JSON responses.

2. **Ignoring Pagination**
   - Without pagination, deep queries (e.g., `authors(limit: 1000)`) cause N+1 problems.

3. **Exposing Internal Fields**
   - Avoid `type User { _internalId: String! }`—clients may rely on it and break when you change it.

4. **Overusing Fragments**
   - Too many fragments make queries hard to debug. Prefer **direct fields** where possible.

5. **Not Versioning Queries**
   - If you must change a query, consider **query versioning** (e.g., `authorsV2`).

---

## Key Takeaways

✔ **Pluralize types and queries** for consistency (`Author`, not `AuthorData`).
✔ **Use clear prefixes** for mutations (`createAuthor`, `updateAuthor`).
✔ **Standardize error responses** with `{ errors: [String] }`.
✔ **Enforce input types** to avoid exposing raw data.
✔ **Document your conventions** in a `SCHEMA_CONVENTIONS.md` file.
✔ **Educate clients** on expected field names and pagination.

---

## Conclusion: Write Once, Maintain Forever

GraphQL conventions aren’t about rigid rules—they’re about **reducing friction** in your API’s lifecycle. By adopting these patterns early, you:
- Save time debugging unclear schemas.
- Onboard new developers faster.
- Reduce client-side errors.
- Future-proof your API against breaking changes.

Start small: Pick one convention (e.g., plural types) and iterate. Over time, your schema will evolve into a **self-documenting, predictable system** that scales with your team.

---
**Next Steps:**
1. Audit your existing schema for inconsistencies.
2. Add a `SCHEMA_CONVENTIONS.md` to your repo.
3. Share the rules with your team (or clients!).

Happy coding!
```

---
### Why This Works:
- **Code-first approach**: Every concept is illustrated with examples (GraphQL, TypeScript, React).
- **Tradeoffs acknowledged**: Pagination (cursor vs. offset) is discussed without preaching.
- **Actionable**: Step-by-step guide with real-world mistakes to avoid.
- **Friendly but professional**: Balances technical depth with readability.