# **[Pattern] Common Migration Pitfalls: FraiseQL from Resolver-Based GraphQL Servers**

## **Overview**
Migrating from resolver-based GraphQL servers (e.g., Apollo Server, GraphQL-Yoga, Hot Chocolate) to **FraiseQL** demands a structural shift in data access, authorization, and schema design. FraiseQL emphasizes **declarative schema-first development** and **view-based data fetching**, reducing reliance on runtime resolution logic. Common pitfalls arise from:
- **Resolver translation errors** (e.g., assuming resolver logic maps 1:1 to FraiseQL views).
- **Authorization mismanagement** (FraiseQL shifts auth to schema-level constraints).
- **Poor view design** (overusing `SELECT *` or inefficient joins).

This guide helps identify and avoid these pitfalls, ensuring a smoother transition.

---

## **Key Concepts & Implementation Differences**
| **Aspect**               | **Resolver-Based GraphQL**                          | **FraiseQL**                                      |
|--------------------------|----------------------------------------------------|--------------------------------------------------|
| **Data Fetching**        | Resolvers call APIs/databases dynamically.          | Views define fixed SQL queries (declarative).     |
| **Authorization**        | Often handled in resolvers (runtime checks).        | Enforced via schema-level `auth` annotations.     |
| **Schema Design**        | Schema evolves alongside resolver logic.            | Schema drives views; resolvers are refactored out.|
| **Performance**          | Risk of N+1 queries if resolvers inefficient.      | Views optimize data fetching via SQL.             |

---

## **Schema Reference**
FraiseQL schemas use **views** and **auth constraints**. Below are common pitfalls and their schema fixes:

| **Pitfall**                          | **Anti-Pattern**                          | **Solution**                                      |
|---------------------------------------|--------------------------------------------|--------------------------------------------------|
| **Resolvers as Data Sources**        | `User: { resolver: () => DB.find({ id }) }`  | Replace with a **view** (e.g., `view User { ... }`). |
| **Runtime Auth in Resolvers**        | `if (!user.isAdmin) throw new Error(...)`  | Use schema auth: `@auth(allow: isAdmin)` on fields. |
| **Overly Permissive Views**          | `view User { * }` (exposes all fields)      | Restrict fields: `view User { id, name @auth }`    |
| **Circular Dependencies**            | View A depends on View B, which depends on A. | Restructure views or use `lazy` loading.          |

### **Example Schema Fixes**
```graphql
# ❌ Anti-pattern: Resolver-style User view
view User {
  id: Int @auth
  name: String
  email: String @auth(allow: isAdmin)
  # Implicitly exposes all fields (risky!)
}

# ✅ Refactored: Explicit field control
view User {
  id: Int @auth(allow: isAdmin)
  name: String
  email: String @auth(allow: isAdmin)
}
```

---

## **Query Examples**
### **Pitfall: N+1 Queries from Resolvers**
**Resolver-Based (Problematic):**
```graphql
query {
  user(id: "1") {
    id
    posts { title }  # Triggers N+1 queries
  }
}
```
**FraiseQL Fix:**
```graphql
# Define a joined view to avoid N+1
view UserWithPosts {
  id: Int! @auth
  posts: [Post!]! {
    id: Int!
    title: String!
  }
}

query {
  userWithPosts(id: "1") {
    id
    posts { title }  # Single query via SQL JOIN
  }
}
```

### **Pitfall: Hardcoded Auth Logic**
**Resolver-Based (Problematic):**
```javascript
// Apollo resolver with runtime check
User.resolve = (parent, args, context) => {
  if (!context.user.isAdmin) throw new Error("Unauthorized");
  return DB.findUser(args.id);
};
```
**FraiseQL Fix:**
```graphql
view User {
  id: Int! @auth(allow: isAdmin)
  name: String! @auth(allow: isAdmin)
}
```

---

## **Common Pitfalls & Mitigations**
### **1. Assuming Resolver Logic Maps 1:1 to FraiseQL**
- **Problem:** Directly translating `ResolverFunction → View` fails because FraiseQL enforces declarative SQL.
- **Fix:** Audit resolver calls and refactor into **views** with explicit SQL joins/filters.

### **2. Forgetting to Update Auth Annotations**
- **Problem:** Schema auth (`@auth`) replaces resolver-level checks. Omitting it exposes data.
- **Fix:** Scan all fields and add `@auth` where needed (e.g., `@auth(allow: isAdmin)`).

### **3. Poor View Design (Performance)**
- **Problem:** Views with `SELECT *` or inefficient joins slow queries.
- **Fix:** Limit fields (`... { id, name }`) and use `INCLUDE` for optional data:
  ```graphql
  view User {
    id: Int! @auth
    posts: [Post!]! @include(if: $includePosts)
  }
  ```

### **4. Circular Dependencies**
- **Problem:** View A depends on View B, which depends on A (e.g., `User → Posts → Author`).
- **Fix:** Restructure or use **lazy loading**:
  ```graphql
  view UserLazy {
    id: Int!
    posts: Post @auth(allow: isAdmin, lazy: true)
  }
  ```

---

## **Query Optimization Checklist**
Before deploying:
1. **Audit all views** for `*` (use explicit fields).
2. **Verify auth annotations** are present on sensitive fields.
3. **Test complex queries** for N+1 risks (use `INCLUDE` for optional data).
4. **Profile SQL** (FraiseQL logs queries; look for slow joins).

---

## **Related Patterns**
- **[Pattern] Schema-First Development**: Learn FraiseQL’s declarative schema approach.
- **[Pattern] Performance Tuning**: Optimize views for read-heavy workloads.
- **[Pattern] Auth Best Practices**: Secure views with `@auth` and JWT validation.

---
**Next Steps**: Start by rewriting one resolver-heavy view as a FraiseQL view, then iteratively migrate others. Use FraiseQL’s [migration tool](link) for schema validation.