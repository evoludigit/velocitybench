# **Debugging [Pattern]: Mapping GraphQL Types to Database Views – A Troubleshooting Guide**

---
## **1. Introduction**
This guide focuses on debugging issues when mapping GraphQL types directly to database views (commonly prefixed with `v_*`). Misalignment between GraphQL schema, database schema, and runtime behavior can lead to frustrating errors. This guide provides a structured approach to identify and resolve common problems efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, quickly validate these symptoms to confirm the issue aligns with this pattern:

| **Symptom**                     | **Possible Cause**                          |
|----------------------------------|--------------------------------------------|
| `ERROR: relation "v_users" does not exist` | View not created in DB |
| `ERROR: column "id" does not exist` | GraphQL type columns mismatch DB view |
| `Missing resolver for GraphQL type` | Resolver written before DB view exists |
| `Runtime errors on schema validation` | Schema sync issue (e.g., deleted view) |
| `Slow query performance` | Complex/unoptimized view or missing indexes |
| `TypeScript errors (unknown type "v_user")` | Schema mismatch (DB vs. GraphQL) |

If multiple symptoms appear, prioritize **database schema consistency** first.

---

## **3. Common Issues & Fixes**

### **Issue 1: View Doesn’t Exist in Database**
#### **Symptoms:**
- `relation "v_users" does not exist` (PostgreSQL) or similar errors in other DBs.
- Works locally but fails in staging/prod (schema drift).

#### **Root Causes:**
- View not created (e.g., backend dev missed deployment).
- View was dropped but not updated in GraphQL schema.
- Database schema was manually altered.

#### **Fixes:**
1. **Verify View Existence**
   ```bash
   # PostgreSQL example
   psql -U <user> -d <db> -c "SELECT * FROM information_schema.views WHERE table_schema = 'public';"
   ```
   - If missing, recreate the view using your database migration tool (e.g., Flyway, Alembic) or SQL directly.

2. **Update GraphQL Schema**
   - If the view was renamed/deleted, update the GraphQL type:
     ```graphql
     # Before (incorrect)
     type v_user {
       id: ID!
       name: String!
     }

     # After (correct)
     type user {
       id: ID!
       name: String!
     }
     ```
   - Regenerate the GraphQL schema (e.g., using `graphql-codegen` or `hasura` metadata).

3. **Automate Schema Sync**
   - Use a tool like **Hasura’s metadata sync** or **Prisma’s introspection** to auto-align schemas.

---

### **Issue 2: Column Mismatch Between View and GraphQL**
#### **Symptoms:**
- `ERROR: column "email" does not exist` (GraphQL expects `email`, but view has `user_email`).
- TypeScript error: `Property 'created_at' does not exist on type 'v_user'`.

#### **Root Causes:**
- GraphQL schema was updated before the view.
- View query changed (e.g., aliased columns).
- Case sensitivity issues (e.g., `CreatedAt` vs `created_at`).

#### **Fixes:**
1. **Compare View Schema**
   ```sql
   -- PostgreSQL: inspect view structure
   \d v_users
   -- OR
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'v_users';
   ```

2. **Update GraphQL Type**
   ```graphql
   # If view has `user_email` but schema expects `email`
   type v_user {
     id: ID!
     user_email: String!  # Renamed field to match view
   }
   ```

3. **Use a Schema Generator Script**
   Auto-generate GraphQL types from the DB (example with Prisma):
   ```bash
   npx prisma db pull
   ```
   Or use tools like `graphql-codegen` with a `resolvers` plugin.

---

### **Issue 3: Resolvers Written Before DB Schema**
#### **Symptoms:**
- `Cannot read property 'map' of undefined` (resolver assumes view exists).
- `Missing resolver for 'v_user'` (schema exists but resolver is incomplete).

#### **Root Causes:**
- Frontend devs wrote resolvers before DB views were ready.
- CI/CD pipeline didn’t enforce schema validation.

#### **Fixes:**
1. **Check Resolver Existence**
   - Ensure resolvers exist for all GraphQL types:
     ```javascript
     // Example resolver stub (placeholder)
     const resolvers = {
       Query: {
         vUsers: async (_, __) => {
           throw new Error("View not implemented yet!");
         },
       },
     };
     ```
   - If missing, add a fallback or redirect to an API that queries the view.

2. **Add Schema Validation in CI**
   - Use `graphql-validation` or `prisma validate` to block schema-resolver mismatches.

3. **Use Feature Flags**
   - Temporarily disable GraphQL queries for in-development views:
     ```graphql
     directives {
       @deprecated(reason: "View v_users not ready")
     }

     type Query {
       vUsers: v_user @deprecated
     }
     ```

---

### **Issue 4: Runtime Errors Due to Missing Views**
#### **Symptoms:**
- `ERROR 42P01: relation does not exist` during runtime (not just compile-time).
- Works in dev but fails in prod (schema drift).

#### **Root Causes:**
- Database migrations weren’t applied.
- CI/CD skipped DB schema updates.

#### **Fixes:**
1. **Check Database State**
   ```bash
   # Example: Verify if migrations were run
   psql -U <user> -d <db> -c "SELECT * FROM <migration_table>;"
   ```
   - If missing, re-run migrations:
     ```bash
     yarn migrate:up
     ```

2. **Add Schema Health Checks**
   - Use a startup script to verify views exist before starting the server:
     ```javascript
     // server.js or entrypoint
     async function checkViews() {
       const client = await pool.connect();
       const res = await client.query('SELECT 1 FROM v_users LIMIT 1');
       if (!res.rows.length) throw new Error("View v_users missing!");
     }
     await checkViews();
     ```

3. **Use Database Transactions for Rollbacks**
   - Ensure all schema changes are transactional (e.g., Flyway `recover`):
     ```bash
     yarn migrate:recover
     ```

---

### **Issue 5: Performance Issues with Views**
#### **Symptoms:**
- Slow response times (e.g., 2s+ for a simple query).
- `TimeoutError` from long-running view queries.

#### **Root Causes:**
- View queries are too complex (nested subqueries, joins).
- Missing indexes on view columns.
- Materialized views not refreshed.

#### **Fixes:**
1. **Optimize View Query**
   - Example: Replace a correlated subquery with a join:
     ```sql
     -- Slow (correlated subquery)
     CREATE VIEW v_user_orders AS
     SELECT u.*, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as order_count
     FROM users u;

     -- Faster (explicit join)
     CREATE VIEW v_user_orders AS
     SELECT u.id, u.name, COUNT(o.id) as order_count
     FROM users u
     LEFT JOIN orders o ON u.id = o.user_id
     GROUP BY u.id, u.name;
     ```

2. **Add Indexes**
   ```sql
   CREATE INDEX idx_v_user_id ON v_user(id);
   ```

3. **Use Materialized Views with Refresh**
   ```sql
   CREATE MATERIALIZED VIEW v_user_stats AS
   SELECT user_id, COUNT(*) as orders
   FROM orders
   GROUP BY user_id;

   -- Refresh periodically (e.g., daily)
   REFRESH MATERIALIZED VIEW v_user_stats;
   ```

---

## **4. Debugging Tools & Techniques**

### **Tool 1: Database Schema Inspection**
- **PostgreSQL**: `\d v_*` (psql), `information_schema.views`.
- **MySQL**: `SHOW CREATE VIEW v_user;`.
- **SQLite**: `.schema v_user`.

### **Tool 2: GraphQL Schema Validation**
- **Hasura**: Use `hasura console > Metadata > Types` to visualize mismatches.
- **Prisma**: `prisma validate` to check schema consistency.
- **GraphQL Playground/Apollo Studio**: Test queries interactively to catch errors early.

### **Tool 3: Logging & Tracing**
- **Database Logs**:
  ```bash
  # Enable PostgreSQL logging for queries
  ALTER SYSTEM SET log_statement = 'all';
  ```
- **GraphQL Resolver Traces**:
  ```javascript
  const debug = require('debug')('graphql:resolvers');
  resolvers.Query = {
    vUsers: async (_, __) => {
      debug("Querying v_users view");
      const result = await pool.query('SELECT * FROM v_users');
      debug("Fetched %d rows", result.rowCount);
      return result.rows;
    },
  };
  ```

### **Tool 4: CI/CD Schema Checks**
- **Pre-push Hook**: Run `prisma validate` or `graphql-codegen`.
  ```bash
  # Example .git/hooks/pre-push
 #!/bin/sh
  npx prisma validate || exit 1
  ```
- **Deployment Checks**:
  ```javascript
  // Example Kubernetes readiness probe
  livenessProbe:
    httpGet:
      path: /health
      queryParam: schemaCheck: "v_users"
  ```

---

## **5. Prevention Strategies**

### **1. Schema as Code**
- **Database**: Use migrations (Flyway, Alembic, Prisma).
- **GraphQL**: Define types in a shared schema file (e.g., `schema.graphql`) and auto-generate resolvers.

### **2. Automated Sync**
- **Hasura**: Use metadata sync to auto-align DB and GraphQL.
- **Custom Scripts**: Run `db-schema-to-graphql` scripts before deployment.

### **3. Feature Flags**
- Disable GraphQL queries for incomplete views:
  ```graphql
  directive @deprecated(reason: String!) on FIELD_DEFINITION

  type Query {
    v_users: [v_user] @deprecated(reason: "View not ready")
  }
  ```

### **4. Testing**
- **Unit Tests**: Mock database responses to test resolvers:
  ```javascript
  test('v_users resolver handles missing view', async () => {
    const mockPool = { query: jest.fn().mockRejectedValue(new Error("View missing")) };
    const resolver = createResolver(mockPool);
    await expect(resolver(null, {})).rejects.toThrow();
  });
  ```
- **Integration Tests**: Verify schema consistency in staging:
  ```bash
  # Example: Run schema checks in GitHub Actions
  - name: Check DB Schema
    run: |
      psql -U user -d db -c "\d v_users" || exit 1
  ```

### **5. Documentation**
- **README Badges**: Add a `schemas` badge linking to live schema docs.
- **Confluence/Notion**: Document view dependencies (e.g., "v_user requires v_user_orders").

### **6. Rollback Plan**
- **Database**: Use migration tools to recover:
  ```bash
  yarn migrate:down  # Rollback last migration
  ```
- **GraphQL**: Temporarily disable the type:
  ```graphql
  type v_user @skip(if: $isDev) {
    id: ID!
  }
  ```

---

## **6. Quick Reference Cheatsheet**
| **Scenario**               | **Command/Check**                          | **Tool**                  |
|----------------------------|--------------------------------------------|---------------------------|
| View doesn’t exist          | `\d v_users`                               | PostgreSQL CLI            |
| Column mismatch             | `information_schema.columns`               | Database Inspector        |
| Resolver missing           | `resolvers.Query.vUsers` check             | Code Editor               |
| Runtime errors              | Check DB logs (`pg_log`)                    | Database Logs             |
| Performance bottlenecks     | `EXPLAIN ANALYZE SELECT * FROM v_users`    | PostgreSQL EXPLAIN        |
| Schema sync                 | `prisma generate`                          | Prisma CLI               |

---

## **7. Final Steps**
1. **Reproduce the Issue**: Confirm symptoms match this guide.
2. **Narrow Down**: Start with database schema checks, then GraphQL.
3. **Fix Incrementally**: Update one view/type at a time.
4. **Test**: Verify fixes in staging before prod.
5. **Document**: Update READMEs or wikis with new schemas.

---
**Pro Tip**: For teams, use **Hasura** or **Prisma** to reduce manual sync work. For solo devs, automate schema checks in CI.

---
**End of Guide**. Happy debugging! 🚀