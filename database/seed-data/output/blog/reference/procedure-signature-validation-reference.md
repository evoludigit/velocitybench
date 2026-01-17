# **[Pattern] Reference Guide: Procedure Signature Validation**

---
## **Overview**
This pattern enforces **compile-time validation** of stored procedure signatures to ensure consistency between mutations and their designated contract logic. By validating parameter names, types, and return values, developers catch mismatches early, reducing runtime errors and enforcing contract compliance.

The pattern is particularly useful when working with **database mutation procedures** (e.g., `UPDATE`, `INSERT`, `DELETE`) that rely on pre-registered contracts (e.g., GraphQL mutations, API endpoints, or ORM mappings). Signature validation prevents silent failures that arise when stored procedures change without updating dependent contracts.

---
## **Key Concepts**
This pattern assumes:

| **Term**                     | **Definition**                                                                 |
|------------------------------|---------------------------------------------------------------------------------|
| **Stored Procedure**         | A database function (e.g., `CREATE PROCEDURE`) used for mutations.              |
| **Mutation Contract**        | A defined interface (e.g., GraphQL mutation schema) specifying parameters/return types. |
| **Signature Validation**     | Runtime/Compile-time checks ensuring procedure parameters match the contract.   |
| **DBML/ORM Reflection**      | Metaprogramming that inspects stored procedures against registered contracts.   |

---
## **Schema Reference**
### **1. Core Tables/Schemas**
| **Entity**               | **Description**                                                                 | **Key Fields**                          |
|--------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| `db_contracts`           | Holds registered mutation contracts (e.g., GraphQL types).                   | `contract_id`, `name`, `version`         |
| `procedure_signatures`   | Maps contracts to stored procedures with expected signatures.                  | `contract_id`, `procedure_name`, `db_schema` |
| `parameters`             | Defines expected input/output parameters per contract.                        | `signature_id`, `param_name`, `type`, `is_input`, `is_required` |
| `return_types`           | Specifies return type for stored procedures.                                | `signature_id`, `return_type`             |

### **2. Example Schema Implementation (PostgreSQL)**
```sql
-- Contracts table
CREATE TABLE db_contracts (
    contract_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(64) NOT NULL,
    schema_text TEXT          -- e.g., GraphQL schema or JSON schema
);

-- Procedure signatures
CREATE TABLE procedure_signatures (
    signature_id SERIAL PRIMARY KEY,
    contract_id INT REFERENCES db_contracts(contract_id),
    procedure_name VARCHAR(255) NOT NULL,
    db_schema VARCHAR(64) NOT NULL,  -- e.g., "public" or "custom_schema"
    db_server VARCHAR(64)           -- For distributed systems
);

-- Parameters
CREATE TABLE parameters (
    param_id SERIAL PRIMARY KEY,
    signature_id INT REFERENCES procedure_signatures(signature_id),
    param_name VARCHAR(255) NOT NULL,
    type VARCHAR(64) NOT NULL,    -- e.g., "INT", "JSONB", "UUID"
    is_input BOOLEAN NOT NULL,
    is_required BOOLEAN DEFAULT TRUE,
    default_value TEXT
);

-- Return types
CREATE TABLE return_types (
    return_id SERIAL PRIMARY KEY,
    signature_id INT REFERENCES procedure_signatures(signature_id),
    return_type VARCHAR(64) NOT NULL
);
```

---
## **Implementation Steps**
### **1. Register Contracts**
Define mutation contracts (e.g., from GraphQL schemas) and link them to stored procedures.

```sql
-- Register a "user_update" contract
INSERT INTO db_contracts (name, version, schema_text)
VALUES ('user_update', '1.0.0', 'mutation UpdateUser($id: ID!, $name: String) { ...}');

-- Link contract to stored procedure
INSERT INTO procedure_signatures (contract_id, procedure_name, db_schema)
VALUES (
    (SELECT contract_id FROM db_contracts WHERE name = 'user_update'),
    'update_user',
    'public'
);
```

### **2. Define Parameter Signatures**
Populate expected parameters for the procedure.

```sql
-- Add parameters to "user_update"
INSERT INTO parameters (signature_id, param_name, type, is_input)
VALUES (
    (SELECT signature_id FROM procedure_signatures
     WHERE procedure_name = 'update_user'),
    'user_id', 'UUID', TRUE
);

INSERT INTO parameters (signature_id, param_name, type, is_input, is_required)
VALUES (
    (SELECT signature_id FROM procedure_signatures
     WHERE procedure_name = 'update_user'),
    'new_name', 'VARCHAR(128)', TRUE, FALSE
);
```

### **3. Set Return Type**
Specify the expected return value (e.g., `USER` type or `JSON`).

```sql
-- Add return type
INSERT INTO return_types (signature_id, return_type)
VALUES (
    (SELECT signature_id FROM procedure_signatures
     WHERE procedure_name = 'update_user'),
    'USER'
);
```

### **4. Validate at Compile/Runtime**
Use a validator (e.g., a database extension or middleware) to check if stored procedures match registered signatures.

---
## **Query Examples**
### **1. Query to Fetch Contract-Specific Parameters**
```sql
SELECT
    p.param_name,
    p.type,
    p.is_required
FROM parameters p
JOIN procedure_signatures ps ON p.signature_id = ps.signature_id
WHERE ps.contract_id = (
    SELECT contract_id FROM db_contracts WHERE name = 'user_update'
);
```
**Output:**
| `param_name` | `type`    | `is_required` |
|--------------|-----------|---------------|
| user_id      | UUID      | TRUE          |
| new_name     | VARCHAR   | FALSE         |

### **2. Query to Check Procedure Existence**
```sql
SELECT
    ps.procedure_name,
    rt.return_type
FROM procedure_signatures ps
JOIN return_types rt ON ps.signature_id = rt.signature_id
WHERE ps.contract_id = (
    SELECT contract_id FROM db_contracts WHERE name = 'user_update'
);
```
**Output:**
| `procedure_name` | `return_type` |
|------------------|---------------|
| update_user      | USER          |

### **3. Validate Against Actual Stored Procedure**
```sql
-- Example: Inspect actual PostgreSQL procedure (using reflection)
SELECT routine_name, argument_data_type
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name = 'update_user';
```
*Compare this output with the registered signature in `parameters` and `return_types`.*

---
## **Validation Logic**
The validator can use the following rules:

| **Rule**                          | **Description**                                                                 |
|-----------------------------------|---------------------------------------------------------------------------------|
| **Parameter Count**               | Stored procedure must have the same number of parameters as the contract.      |
| **Parameter Order**               | Parameters must match in order (e.g., `($id, $name)`).                        |
| **Parameter Types**               | Types must align (e.g., `UUID` != `INT`).                                      |
| **Return Type**                   | Stored procedure’s return type must match the contract.                         |
| **Default Values**                | `is_required = FALSE` parameters must allow `NULL` or have defaults.          |

---
## **Error Handling**
| **Error Type**            | **Example**                                      | **Solution**                                  |
|---------------------------|--------------------------------------------------|-----------------------------------------------|
| Missing Parameter         | Contract expects `user_id`, but procedure lacks it. | Update contract or procedure.                 |
| Type Mismatch             | Contract expects `UUID`, procedure uses `VARCHAR`. | Align types in contract or procedure.          |
| Extra Parameter           | Procedure has `email` input, but contract doesn’t. | Remove extra parameter or update contract.    |
| Return Type Mismatch      | Contract expects `USER`, procedure returns `JSON`. | Adjust return type in contract or procedure. |

---
## **Related Patterns**
1. **Procedure Tagging**
   - Annotate stored procedures with metadata (e.g., `@contract="user_update"`) to automate signature mapping.
   - *See: [Procedure Tagging Pattern](link-to-pattern)*.

2. **Schema Evolution Control**
   - Use **backward-compatible mutations** (e.g., optional parameters) to handle schema changes.
   - *See: [Schema Evolution Strategy](link-to-pattern)*.

3. **Dependency Graph Tracking**
   - Maintain a graph of dependent contracts to flag breaking changes early.
   - *See: [Dependency Graph Pattern](link-to-pattern)*.

4. **Runtime Contract Enforcement**
   - Use middleware (e.g., API gateways) to validate procedure calls against contracts at runtime.
   - *See: [Runtime Validation Layer](link-to-pattern)*.

---
## **Tools & Libraries**
| **Tool**               | **Use Case**                                                                 |
|------------------------|------------------------------------------------------------------------------|
| **DBML Generators**    | Auto-generate contract schemas from database metadata.                      |
| **ORM Reflection**     | Tools like Prisma, Flyway, or custom scripts to sync contracts with DB.     |
| **GraphQL Validators** | Integrate with GraphQL schema validators (e.g., GraphQL Code Generator).    |
| **CI/CD Pipelines**    | Run validation checks during deployment to catch signature drifts.          |

---
## **Best Practices**
1. **Document Contract Changes**
   Use versioned contracts (e.g., `db_contracts.version`) to track schema updates.

2. **Automate Validation**
   Embed checks in CI/CD pipelines (e.g., pre-deploy tests).

3. **Support Deprecation**
   Allow phased rollouts by marking contracts as `is_deprecated`.

4. **Logging & Alerts**
   Log signature mismatches and alert teams to resolve issues before runtime.

5. **Test with Mock Procedures**
   Use in-memory databases (e.g., SQLite) to test contract validation without touching production.

---
## **Example Workflow**
1. **Developer** updates `user_update` procedure to accept `email`:
   ```sql
   CREATE OR REPLACE PROCEDURE public.update_user(
       user_id UUID,
       new_name VARCHAR(128),
       email VARCHAR(255)  -- NEW PARAMETER
   ) ...
   ```

2. **Validation Fails**:
   The system detects `email` doesn’t exist in the `user_update` contract and raises:
   ```
   ERROR: Procedure 'update_user' has 3 parameters, but contract expects 2.
   Missing parameter: 'email'.
   ```

3. **Developer** updates the contract:
   ```sql
   ALTER TABLE parameters INSERT INTO (
       signature_id, param_name, type, is_input, is_required
   ) VALUES (
       (SELECT signature_id FROM procedure_signatures WHERE procedure_name = 'update_user'),
       'email', 'VARCHAR(255)', TRUE, FALSE
   );
   ```

---
## **Limitations**
| **Challenge**                | **Workaround**                                  |
|------------------------------|------------------------------------------------|
| Dynamic SQL Procedures       | Use reflection APIs to inspect parameters at runtime. |
| Legacy Databases             | Implement custom validators for unsupported DBs. |
| Schema Drift Without Alerts  | Enforce versioned contracts and auto-alerts.    |

---
## **Further Reading**
- [GraphQL Schema Validation](https://graphql.org/learn/schema/)
- [PostgreSQL Routine Reflection](https://www.postgresql.org/docs/current/sql-routines.html)
- [ORM Schema Migrations](https://migrations.prisma.io/)