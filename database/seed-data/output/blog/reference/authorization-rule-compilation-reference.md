**[Pattern] Reference Guide: Authorization Rule Compilation**

---

### **1. Overview**
The **Authorization Rule Compilation** pattern ensures authorization decisions are statically enforced by embedding rules directly into metadata during schema compilation. Rather than evaluating policies at runtime (risking bypass), rules are pre-processed into immutable table definitions or view constraints, enabling compiler-level validation, query optimization, and security guarantees. This approach is ideal for high-assurance systems where runtime flexibility is sacrificed for robustness (e.g., databases, blockchain, or safety-critical applications).

Key advantages:
- **Immutable enforcement**: Rules cannot be modified or bypassed at runtime.
- **Static analysis**: Rules are validated during schema design (e.g., syntax, consistency).
- **Query optimization**: Compilers leverage static metadata to prune unauthorized data early.
- **Performance**: Avoids per-row runtime checks.

**Trade-offs**:
- Inflexibility: Rules are fixed at compile time; dynamic policies require schema redeployment.
- Complexity: Requires careful schema design to express rules without redundant metadata.

---

### **2. Schema Reference**

#### **Core Metadata Table Structure**
All authorization rules are encoded as **schema-level metadata** in tables. Below are standard table definitions used in this pattern.

| **Field**          | **Type**          | **Description**                                                                                                                                                                                                 | **Notes**                                                                                     |
|--------------------|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| `rule_id`          | `VARCHAR(255)`    | Unique identifier for the rule (e.g., `user_create_document`).                                                                                                                                                     | Primary key.                                                                                   |
| `scope`            | `ENUM`            | Scope of application: `database`, `table`, `column`, or `row`.                                                                                                                                                   | Used to resolve rule context during query parsing.                                             |
| `entity_type`      | `VARCHAR(255)`    | Type of entity the rule applies to (e.g., `document`, `user`, `file`).                                                                                                                                                | Required for scoped rules (e.g., `table`-level rules apply to all rows in `entity_type`).     |
| `condition`        | `JSON`            | Compiled rule logic as a JSON-encoded expression (e.g., `{"predicate": "user_id == '123'"}`).                                                                                                               | See [Expression Syntax](#expression-syntax) for details.                                      |
| `action`           | `ENUM`            | Permitted action: `read`, `write`, `delete`, or `execute`.                                                                                                                                                     | Multi-value allowed (e.g., `["read", "write"]`).                                               |
| `target`           | `JSON`            | Targets of the rule (e.g., `{"column": "title"}` for column-level access).                                                                                                                                    | Omitted for row/table-level rules.                                                             |
| `metadata`         | `JSON`            | Rule-specific metadata (e.g., `{"compiler": "PostgreSQL", "version": "1.0"}`).                                                                                                                                  | Used for debugging and compatibility.                                                          |

---

#### **Example Rule Tables**
##### **1. Table-Level Rule (Permissions for `documents` table)**
```sql
CREATE TABLE system_rules (
    rule_id VARCHAR(255) PRIMARY KEY,
    scope VARCHAR(20),
    entity_type VARCHAR(255),
    condition JSON,
    action VARCHAR(20)[],
    target JSON,
    metadata JSON
);

-- Rule: Users can only read documents in their "department".
INSERT INTO system_rules VALUES (
    'read_document_by_department',
    'table',
    'document',
    '{"predicate": "author_id = session_user_id AND department = user_department"}',
    ARRAY['read'],
    NULL,
    '{"notes": "Compiled from policy X"}'
);
```

##### **2. Column-Level Rule (Masking sensitive data)**
```sql
-- Rule: Hide SSN from non-admins.
INSERT INTO system_rules VALUES (
    'mask_ssn_column',
    'column',
    'user',
    '{"predicate": "is_admin = false"}',
    ARRAY['read'],
    '{"column": "ssn"}',
    '{"compiler": "PostgreSQL"}'
);
```

---

#### **Expression Syntax**
Rules use a **predicate-based JSON schema** for conditions. Supported operators:
| **Operator** | **Syntax**       | **Example**                     | **Description**                                      |
|--------------|------------------|---------------------------------|------------------------------------------------------|
| Equality     | `==`, `!=`       | `{"predicate": "field == value"}` | Exact match.                                         |
| Logical AND  | `&&`             | `{"predicate": "A && B"}`       | Combined conditions.                                  |
| Comparison   | `<`, `>`, `<=`, `>=` | `{"predicate": "x > 10"}`      | Numeric comparisons.                                  |
| IN           | `IN (...)`       | `{"predicate": "status IN (1, 2)"}` | Membership test.                                     |
| Session vars | `session_*`      | `{"predicate": "session_user_id == user_id"}` | Access runtime context (e.g., `session_user_id`).   |

**Functions**:
- `length()`: `{"predicate": "length(name) > 3"}`.
- `now()`: `{"predicate": "created_at > now() - interval '1 day'"}`.

**Example**:
```json
{
  "predicate": "
    (is_active == true) &&
    (department == session_user_department) &&
    (length(title) <= 100)
  "
}
```

---

#### **Query Processing Integration**
Compiled rules are embedded as **table constraints** or **view definitions**. Example for PostgreSQL:
```sql
-- Generated view with row-level security (RLS) applied.
CREATE VIEW secure_documents AS
SELECT * FROM documents
WHERE EXISTS (
    SELECT 1 FROM system_rules
    WHERE rule_id = 'read_document_by_department'
    AND condition->>'predicate' = '{"predicate": "author_id = session_user_id AND department = user_department"}'
    LIMIT 1
);
```

---

### **3. Query Examples**

#### **Scenario 1: Row-Level Filtering**
**Query**:
```sql
SELECT * FROM documents WHERE department = 'engineering';
```
**Compiled Behavior**:
- The database enforces the `read_document_by_department` rule **before** executing the query, filtering rows where `author_id != session_user_id` or `department != session_user_department`.

#### **Scenario 2: Column Masking**
**Query**:
```sql
SELECT ssn FROM users WHERE id = 42;
```
**Compiled Behavior**:
- The `mask_ssn_column` rule redirects this to a **virtual column** that returns `NULL` for non-admins:
  ```sql
  ALTER TABLE users ADD COLUMN ssn_masked VARCHAR(20)
    GENERATED ALWAYS AS (
      CASE WHEN is_admin THEN ssn ELSE NULL END
    ) STORED;
  ```

#### **Scenario 3: Dynamic Rule Loading (Advanced)**
If rules must occasionally update (e.g., role changes), use a **schema-aware migration**:
```sql
-- Step 1: Parse new rule (e.g., via API).
-- Step 2: Generate SQL and execute:
INSERT INTO system_rules (...);
ALTER TABLE documents ADD CONSTRAINT enforce_read_rule
    CHECK (
        EXISTS (
            SELECT 1 FROM system_rules
            WHERE rule_id = 'read_document_by_department'
            AND condition->>'predicate' = '{"predicate": "..."}'
        )
    );
```

---

### **4. Related Patterns**
| **Pattern**                  | **Description**                                                                                     | **Use Case**                                                                                     |
|------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Policy as Code**           | Define policies in a high-level language (e.g., Open Policy Agent Rego) and compile to metadata.   | Hybrid flexibility (rules can be updated without schema changes).                               |
| **Attribute-Based Access**   | Enforce rules based on user attributes (e.g., `role = "admin"`).                                   | Role-based systems where static rules suffice.                                                 |
| **Row-Level Security (RLS)** | Database-native RLS (e.g., PostgreSQL `ROW LEVEL SECURITY`).                                       | When the database already provides compile-time rule enforcement.                              |
| **Capability-Based Auth**    | Issue capabilities (tokens) at compile time; runtime checks validate token presence.               | Systems where capabilities are immutable (e.g., blockchain).                                   |
| **Dynamic Views**            | Materialize views with pre-applied rules (e.g., `CREATE VIEW secure_users AS SELECT ...`).         | Performance-critical scenarios with static rules.                                               |

---

### **5. Implementation Checklist**
1. **Schema Design**:
   - Define `system_rules` table with the above schema.
   - Document [expression syntax](#expression-syntax) for teams.

2. **Compiler Integration**:
   - **Phase 1**: Parse rules during schema compilation, validate syntax.
   - **Phase 2**: Generate constraints/views based on rules.
   - **Phase 3**: Integrate with query optimizer (e.g., pass rule metadata to the planner).

3. **Runtime**.
   - Ensure no path bypasses compiled rules (e.g., disable `UNCHECKED` constraint enforcement).
   - Log rule violations for auditing.

4. **Testing**:
   - **Static**: Lint rules for syntax errors (e.g., missing `session_user_id`).
   - **Dynamic**: Verify queries respect rules (e.g., `SELECT * FROM documents` returns no rows for unauthorized users).

5. **Scaling**:
   - For large rule sets, partition `system_rules` by `scope` or `entity_type`.
   - Use indexed views for frequently accessed rules.

---
**See Also**:
- [Compiler Design Patterns: Metadata Compilation](link)
- [Database Security: Static Analysis](link)