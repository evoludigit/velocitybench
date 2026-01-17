**[Pattern] Result Projection from JSONB: Reference Guide**

---
### **Overview**
The **Result Projection from JSONB** pattern transforms database query results into GraphQL responses by extracting specific fields from JSONB-formatted database records. This approach ensures efficient data retrieval and structured output, aligning with GraphQL’s non-resolvers approach for simple or semi-structured data.

This pattern is ideal for systems where:
- Database columns store nested or semi-structured data (e.g., `jsonb` in PostgreSQL).
- GraphQL clients request subsets of fields without requiring bespoke resolver logic.
- Performance optimization is critical (e.g., avoiding full table scans or redundant joins).

Key assumptions:
1. Database views or tables output JSONB objects (e.g., `{"id": 1, "meta": {"key": "value"}}`).
2. GraphQL response shapes are static or dynamically derived from input fields.
3. JSONB path extraction is done via SQL (e.g., PostgreSQL’s `jsonb_path_query` or `jsonb_extract_path`).

---

### **Schema Reference**

#### **1. Database Schema Assumptions**
| Column          | Type         | Description                                                                 |
|-----------------|--------------|-----------------------------------------------------------------------------|
| `result_data`   | `jsonb`      | Stores semi-structured data (e.g., `{"user": {"name": "Alice"}, "tags": [...]}`). |
| `created_at`    | `timestamp`  | Standard metadata field.                                                     |
| `id`            | `uuid`       | Primary key.                                                                  |

**Example View:**
```sql
CREATE VIEW user_profiles AS
SELECT
    id,
    jsonb_build_object(
        'name', name,
        'preferences', jsonb_agg(
            jsonb_build_object('theme', theme, 'notifications', enabled)
        )
    ) AS user_data,
    created_at
FROM users
GROUP BY id;
```

---

#### **2. GraphQL Schema**
```graphql
type UserProfile {
  id: ID!
  name: String!
  preferences: [Preference!]!
  createdAt: DateTime!
}

type Preference {
  theme: String!
  notifications: Boolean!
}

type Query {
  userProfile(id: ID!): UserProfile
}
```

---
#### **3. JSONB Path Mapping**
| GraphQL Field       | JSONB Path (PostgreSQL)          | Notes                          |
|--------------------|----------------------------------|--------------------------------|
| `name`             | `result_data->>'name'`           | Direct scalar extraction.       |
| `preferences`      | `result_data->'preferences'`     | Array of objects.              |
| `preferences.theme`| `result_data->'preferences'->>'theme'` | Nested array/object access. |

---
#### **4. Supported JSONB Operations**
| Operation               | PostgreSQL Syntax               | Example Output                          |
|-------------------------|----------------------------------|-----------------------------------------|
| Scalar extraction       | `jsonb_data->>'key'`             | `"Alice"`                              |
| Nested object           | `jsonb_data->'nested'`           | `{"subkey": "value"}`                  |
| Array access            | `jsonb_data->'array'[0]`         | `{"id": 1}` (first element)            |
| Wildcard projection     | `jsonb_data`                     | Full JSONB object                       |

---

### **Query Examples**

#### **1. Simple Projection (Single Field)**
**GraphQL Query:**
```graphql
query {
  userProfile(id: "123e4567-e89b-12d3-a456-426614174000") {
    name
  }
}
```

**PostgreSQL Query:**
```sql
SELECT
    id,
    result_data->>'name' AS name
FROM user_profiles
WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```

---

#### **2. Nested Projection (Array of Objects)**
**GraphQL Query:**
```graphql
query {
  userProfile(id: "123e4567-e89b-12d3-a456-426614174000") {
    preferences {
      theme
    }
  }
}
```

**PostgreSQL Query:**
```sql
SELECT
    id,
    (result_data->'preferences') AS preferences
FROM user_profiles
WHERE id = '123e4567-e89b-12d3-a456-426614174000';
```
**Note:** GraphQL resolver maps the JSONB array to the `Preference` type.

---

#### **3. Dynamic Field Projection (Using `jsonb_path_query`)**
**GraphQL Query:**
```graphql
query {
  userProfile(id: "123e4567-e89b-12d3-a456-426614174000") {
    ... on UserProfile {
      # Dynamic fields (e.g., from query variables)
      dynamicField(key: "name")
    }
  }
}
```

**PostgreSQL Query (Resolver Logic):**
```sql
-- Pseudo-code for resolver:
SELECT
    result_data->>'$key' AS dynamicField
FROM user_profiles
WHERE id = :id;
```
**GraphQL Resolver (e.g., Apollo Server):**
```javascript
resolver: async (parent, args, { dataSources }) => {
  const { id } = args;
  const key = args.dynamicField.key;
  const result = await dataSources.db.query(
    `SELECT (result_data->'${key}') AS dynamicField FROM user_profiles WHERE id = $1`,
    [id]
  );
  return result.rows[0].dynamicField;
};
```

---

#### **4. Performance Optimization (Indexing)**
**Index for Faster JSONB Access:**
```sql
CREATE INDEX idx_user_profiles_name ON user_profiles
USING GIN ((result_data->>'name'));
```

**Justification:**
- Speeds up queries filtering or projecting from `name`.
- Works with `jsonb_path_ops` GIN indexes.

---

### **Implementation Steps**
1. **Database Layer:**
   - Store data in `jsonb` columns or views with structured objects.
   - Use `jsonb_path_query` or direct field extraction (e.g., `->>'key'`) for projections.

2. **GraphQL Layer:**
   - Define types matching JSONB structure.
   - Use **non-resolver projections** for simple fields (e.g., `name`).
   - For complex queries, implement resolvers using SQL `jsonb_path_query`.

3. **Resolver Pattern:**
   - **Option 1 (Direct Projection):**
     ```graphql
     type Query {
       userProfile(id: ID!): UserProfile @awsappsync(projection: "result_data")
     }
     ```
     *(AWS AppSync syntax; equivalent logic applies to other platforms.)*
   - **Option 2 (Resolver Function):**
     ```javascript
     // Example in GraphQL Yoga/Apollo
     const resolvers = {
       Query: {
         userProfile: async (_, { id }, { db }) => {
           const { name, preferences } = await db.query(
             `SELECT result_data FROM user_profiles WHERE id = $1`,
             [id]
           );
           return { name, preferences };
         },
       },
     };
     ```

---

### **Error Handling**
| Issue               | Mitigation Strategy                                |
|---------------------|----------------------------------------------------|
| Missing JSONB key   | Return `null` or default value in SQL.             |
| Query injection     | Sanitize inputs (e.g., validate `key` in resolvers).|
| Large JSONB payload | Stream results or paginate with `LIMIT/OFFSET`.     |

**Example (Safe Query):**
```sql
-- Use parameterized queries to avoid injection
SELECT (result_data->$1) AS value
FROM user_profiles
WHERE id = $2;
```

---

### **Related Patterns**
1. **[Field-Level Authorization in GraphQL]**
   - Combine with this pattern to restrict JSONB field access based on roles.
   - Example: Filter `user_data` in SQL before projection.

2. **[SQL Projections for Complex GraphQL Types]**
   - Use `jsonb_agg` and `jsonb_build_object` to flatten complex data into GraphQL-compatible shapes.

3. **[Dynamic GraphQL Schema Evolution]**
   - Dynamically generate GraphQL types from JSONB schemas (e.g., using `jsonb_typeof`).

4. **[Denormalized JSONB for Performance]**
   - Precompute and store aggregated JSONB data (e.g., `user_profiles` from `users` table).

5. **[GraphQL Persisted Queries with JSONB]**
   - Use hashed query IDs to cache `jsonb`-projected results.

---

### **Anti-Patterns**
- **Overusing Resolvers for Every Query:**
  - Avoid writing custom SQL for simple field projections (defeats performance gains).
- **Ignoring JSONB Indexes:**
  - Without GIN indexes, `jsonb_path_query` operations become slow.
- **Circumventing GraphQL Type Safety:**
  - Let GraphQL enforce types; don’t return raw `jsonb` unless necessary.

---
### **Tools & Libraries**
| Tool/Library          | Purpose                                                                 |
|-----------------------|-------------------------------------------------------------------------|
| PostgreSQL `jsonb_path_query` | Extract nested fields dynamically.                                   |
| AWS AppSync Projections | Define projections in GraphQL schema (no resolver needed).            |
| Hasura `jsonb` Filters | Filter and project JSONB fields via Hasura’s introspection.          |
| GraphQL Yoga/Apollo   | Custom resolvers for complex projections.                              |

---
### **Example Workflow (Full Cycle)**
1. **Client Request:**
   ```graphql
   query {
     userProfile(id: "123") {
       name
       preferences {
         theme
       }
     }
   }
   ```
2. **GraphQL Server (Apollo):**
   - No resolver for `name` (projected directly).
   - Resolver for `preferences`:
     ```javascript
     preferences: async (parent) => {
       return parent.result_data.preferences;
     }
     ```
3. **Database Query:**
   ```sql
   SELECT result_data FROM user_profiles WHERE id = '123';
   ```
4. **Response:**
   ```json
   {
     "data": {
       "userProfile": {
         "name": "Alice",
         "preferences": [{ "theme": "dark" }]
       }
     }
   }
   ```