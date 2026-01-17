# **[Pattern] Mutation Execution via Stored Procedures – Reference Guide**

---
### **Overview**
The **Mutation Execution via Stored Procedures** pattern delegates GraphQL mutation logic to the database by encapsulating business rules, validation, and data manipulation in stored procedures (SPs). This approach ensures **data integrity**, **performance optimization**, and **centralized control** over mutations, reducing server-side complexity. By offloading execution to the database, the pattern minimizes client-server round trips, enhances security (via SP permissions), and leverages database-specific optimizations (e.g., transactions, triggers). However, it requires careful schema design to bridge GraphQL’s flexible type system with rigid SP parameters.

---

### **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Stored Procedure**      | A precompiled SQL script stored in the database that encapsulates business logic for mutations (e.g., `CREATE`, `UPDATE`, `DELETE`).                                                   |
| **GraphQL Mutation**      | A GraphQL operation that triggers a stored procedure execution via a resolver or middleware.                                                                                                          |
| **SP Input/Output Binding**| Maps GraphQL mutation arguments to SP parameters and results to GraphQL return types (e.g., using JSON or table types).                                                                         |
| **Transaction Management** | Database transactions wrap SP calls to maintain ACID compliance across multiple mutations.                                                                                                            |
| **Error Handling**        | SPs return error codes or messages (e.g., `SQLSTATE`) that GraphQL resolvers translate into user-friendly errors.                                                                                     |
| **Security**              | SP permissions (e.g., `EXECUTE`) are scoped to prevent unauthorized access, while GraphQL auth middleware validates user roles before SP invocation.                                                |

---

### **Schema Reference**
Below is a schema example for a **User Management** system using stored procedures for mutations. GraphQL types are mapped to SP inputs/outputs.

#### **GraphQL Schema**
```graphql
type User {
  id: ID!
  username: String!
  email: String!
  role: Role!
}

enum Role {
  ADMIN
  EDITOR
  VIEWER
}

type Query {
  getUser(id: ID!): User
}

type Mutation {
  # SP: CreateUser
  createUser(input: CreateUserInput!): User!

  # SP: UpdateUser
  updateUser(id: ID!, input: UpdateUserInput!): User!

  # SP: DeleteUser
  deleteUser(id: ID!): Boolean!
}

input CreateUserInput {
  username: String!
  email: String!
  role: Role!
}

input UpdateUserInput {
  username: String
  email: String
  role: Role
}
```

#### **Database Schema (PostgreSQL Example)**
```sql
-- SP: CreateUser
CREATE OR REPLACE FUNCTION create_user(
  p_username TEXT,
  p_email TEXT,
  p_role VARCHAR(20)
) RETURNS TABLE (
  id SERIAL PRIMARY KEY,
  username TEXT,
  email TEXT,
  role VARCHAR(20)
) AS $$
BEGIN
  RETURN QUERY
  INSERT INTO users (username, email, role)
  VALUES (p_username, p_email, p_role)
  RETURNING *;
END;
$$ LANGUAGE plpgsql;

-- SP: UpdateUser
CREATE OR REPLACE FUNCTION update_user(
  p_id INTEGER,
  p_username TEXT,
  p_email TEXT,
  p_role VARCHAR(20)
) RETURNS TABLE (
  id INTEGER,
  username TEXT,
  email TEXT,
  role VARCHAR(20)
) AS $$
BEGIN
  UPDATE users
  SET username = COALESCE(p_username, username),
      email = COALESCE(p_email, email),
      role = COALESCE(p_role, role)
  WHERE id = p_id
  RETURNING *;
END;
$$ LANGUAGE plpgsql;
```

#### **SP-GraphQL Mapping Table**
| **GraphQL Mutation**       | **SP Name**          | **Input Parameters**               | **Return Type**       | **Security Context**       |
|----------------------------|----------------------|-------------------------------------|-----------------------|----------------------------|
| `createUser`               | `create_user`        | `username`, `email`, `role`         | `User` (recordset)    | `GRANT EXECUTE ON create_user TO graphql_user;` |
| `updateUser`               | `update_user`        | `id`, `username`, `email`, `role`   | `User` (recordset)    | Same as above               |
| `deleteUser`               | `delete_user` (custom)| `id`                                | `Boolean`             | Requires `DELETE` privilege on `users` |

---
### **Query Examples**
#### **1. Create a User**
**GraphQL Mutation:**
```graphql
mutation {
  createUser(input: {
    username: "alice123",
    email: "alice@example.com",
    role: EDITOR
  }) {
    id
    username
  }
}
```

**SP Invocation (Resolver Logic):**
```javascript
const { createUser } = require('./database');

exports.createUser = async (_, { input }) => {
  const { rows } = await createUser(input.username, input.email, input.role);
  return rows[0]; // Return first inserted record
};
```

**Output:**
```json
{
  "data": {
    "createUser": {
      "id": 1,
      "username": "alice123"
    }
  }
}
```

---

#### **2. Update a User’s Role**
**GraphQL Mutation:**
```graphql
mutation {
  updateUser(id: 1, input: { role: ADMIN }) {
    role
  }
}
```

**SP Invocation:**
```javascript
const { updateUser } = require('./database');

exports.updateUser = async (_, { id, input }) => {
  const { rows } = await updateUser(id, input.username, input.email, input.role);
  return rows[0];
};
```

**Output:**
```json
{
  "data": {
    "updateUser": {
      "role": "ADMIN"
    }
  }
}
```

---

#### **3. Delete a User**
**GraphQL Mutation:**
```graphql
mutation {
  deleteUser(id: 1)
}
```

**Custom SP (PostgreSQL Example):**
```sql
CREATE OR REPLACE FUNCTION delete_user(p_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS(DELETE FROM users WHERE id = p_id RETURNING 1);
END;
$$ LANGUAGE plpgsql;
```

**Resolver Logic:**
```javascript
const { deleteUser } = require('./database');

exports.deleteUser = async (_, { id }) => {
  const result = await deleteUser(id);
  return result.exists; // Assuming SP returns a JSON object
};
```

**Output:**
```json
{
  "data": {
    "deleteUser": true
  }
}
```

---

### **Error Handling**
SPs should return standardized error codes or messages. Example:

**SP Failure Case (`create_user`):**
```sql
CREATE OR REPLACE FUNCTION create_user(...)
RETURNS TABLE (...) AS $$
BEGIN
  IF EXISTS(SELECT 1 FROM users WHERE email = p_email) THEN
    RAISE EXCEPTION 'Email already exists';
  END IF;
  -- Rest of the SP...
END;
$$;
```

**GraphQL Resolver (Error Translation):**
```javascript
exports.createUser = async (_, { input }) => {
  try {
    const { rows } = await createUser(input.username, input.email, input.role);
    return rows[0];
  } catch (error) {
    if (error.message.includes('Email already exists')) {
      throw new Error('Email is already in use.');
    }
    throw error;
  }
};
```

**Client-Side Error Response:**
```json
{
  "errors": [
    {
      "message": "Email is already in use."
    }
  ]
}
```

---

### **Performance Considerations**
1. **Batch Operations**: Use `RETURNS TABLE` to return multiple records in a single SP call.
2. **Indexing**: Ensure SP parameters (e.g., `id`) are indexed in the database.
3. **Connection Pooling**: Reuse database connections for high-throughput mutations.
4. **Avoid N+1 Queries**: Fetch related data (e.g., user permissions) in a single SP call.

---
### **Security Best Practices**
1. **Least Privilege**: Grant SP execution rights only to authenticated roles.
   ```sql
   GRANT EXECUTE ON create_user TO graphql_user;
   ```
2. **Input Validation**: Validate SP parameters server-side (e.g., check `email` format).
3. **SQL Injection Prevention**: Use parameterized queries (SPs inherently prevent this).
4. **Audit Logging**: Log SP executions and changes via database triggers.

---
### **Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[Data Loader](https://graphql.org/learn/best-practices/#data-loading)** | Batch and cache SP calls to reduce database load.                                                                                                                                                        |
| **[Query Execution via Stored Procedures](https://)** | Similar to mutations, but for `query` operations (read-only SPs).                                                                                                                                       |
| **[GraphQL Schema Stitching](https://www.apollographql.com/docs/apollo-server/data/stitching/)** | Combine mutations from multiple SP sources (e.g., microservices) under one GraphQL schema.                                                                                               |
| **[Optimistic Locking](https://martinfowler.com/eaaCatalog/optimisticOffline.html)** | Use SP-based versioning (e.g., `timestamp` or `row_version`) to handle concurrent mutations.                                                                                                     |
| **[GraphQL Subscriptions](https://graphql.org/learn/subscriptions/)** | Complement mutations with real-time updates via SP-triggered events (e.g., PostgreSQL `LISTEN/NOTIFY`).                                                                                     |

---
### **Tools and Libraries**
| **Tool/Library**               | **Purpose**                                                                                                                                                                                                 |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Prisma**                      | Auto-generates SP-like mutations for databases (supports custom SQL).                                                                                                                                |
| **DgraphQL**                    | GraphQL over Dgraph, with SP-like query/mutation support via `txn`.                                                                                                                                   |
| **Hasura**                      | Automates SP-like mutations via event triggers and remote schema integration.                                                                                                                   |
| **TypeORM/Sequelize**          | Supports custom SP execution via `QueryBuilder` or direct SQL templates.                                                                                                                           |
| **PostgreSQL `jsonb`**          | Simplifies SP input/output by serializing GraphQL objects (e.g., `CREATE FUNCTION update_user(p_user jsonb)`).                                                                                   |

---
### **When to Use This Pattern**
✅ **Use when**:
- Business logic is **complex** and best suited for the database (e.g., financial calculations, compliance checks).
- You need **fine-grained permissions** (e.g., SP-level access control).
- **Performance** requires minimizing client-server round trips (e.g., bulk operations).
- The database is a **trusted environment** (e.g., no arbitrary code execution risks).

❌ **Avoid when**:
- Mutations are **simple CRUD** (use resolvers directly).
- The database lacks **SP support** (e.g., SQLite).
- **Real-time updates** are required (consider subscriptions + SP triggers).
- You need **flexible schema evolution** (SPs can be rigid to modify).

---
### **Example Workflow (Full Stack)**
1. **Client** sends a mutation:
   ```graphql
   mutation { createUser(input: { username: "bob", email: "bob@example.com" }) }
   ```
2. **GraphQL Server** validates input → calls SP via resolver.
3. **Database** executes `create_user("bob", "bob@example.com", "VIEWER")` → returns record.
4. **Server** returns data to client or broadcasts via subscriptions.

---
### **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                                     |
|-------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **SP returns NULL**                 | Missing `RETURNING` clause or no rows affected.                                | Ensure `RETURNING *` or explicit columns are included.                                             |
| **GraphQL error: "Parameter missing"** | SP parameter name mismatch.                                                  | Align GraphQL input names with SP parameters (e.g., `p_username` vs. `username`).               |
| **Permission denied**               | SP lacks `EXECUTE` permission.                                              | Grant permissions: `GRANT EXECUTE ON sp_name TO role;`                                            |
| **Slow mutations**                  | No indexes on SP parameters or N+1 queries.                                    | Add indexes or fetch related data in a single SP call (e.g., `JOIN`).                             |

---
### **Further Reading**
- [PostgreSQL Stored Procedures](https://www.postgresql.org/docs/current/plpgsql.html)
- [SQL Server CLR Stored Procedures](https://learn.microsoft.com/en-us/sql/relational-databases/programming/clr-integration-sql-server?view=sql-server-ver16)
- [GraphQL Mutations Best Practices](https://www.howtographql.com/basics/5-mutations/)