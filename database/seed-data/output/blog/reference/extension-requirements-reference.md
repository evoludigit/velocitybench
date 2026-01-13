# **[Extension Requirements] Reference Guide**

## **Overview**

Extensions in PostgreSQL (e.g., `pgvector`, `postgis`) enhance database functionality by providing custom data types, operators, functions, and indexing capabilities. The **Extension Requirements** pattern ensures that extensions are properly installed, configured, and compatible with the application schema. This guide outlines the key concepts, schema considerations, common queries, and related patterns for managing extension dependencies.

This pattern applies to:
- **Extensions with dependencies** (e.g., `pgvector` requiring `postgis` or custom functions).
- **Schema validation** before extension use.
- **Dynamic extension checks** in production environments.

---

## **Implementation Details**

### **Key Concepts**

1. **Extension Dependency Graph**
   - Extensions may depend on other extensions (e.g., `pgvector` requires `postgis` for spatial operations).
   - Missing dependencies result in `ERROR: extension "extension_name" requires library "libname"`.

2. **Schema Modifications**
   - Extensions introduce new tables, data types (e.g., `vector`, `geometry`), and functions.
   - Applications must account for these changes in migrations or DDL scripts.

3. **Dynamic Checks**
   - Validate extensions at runtime (e.g., via `pg_available_extensions()` or custom scripts).

4. **Rollback Considerations**
   - Extensions alter the database state; rollback must drop tables and types safely.

---

## **Schema Reference**

| **Component**       | **Details**                                                                                     | **Example**                          |
|---------------------|-------------------------------------------------------------------------------------------------|---------------------------------------|
| **Extension Status** | Query to check if an extension exists and is installed.                                         | `SELECT * FROM pg_available_extensions WHERE name = 'pgvector';` |
| **Extension Dependencies** | List of dependencies required by an extension.                                                    | `SELECT * FROM pg_extension_depends WHERE extname = 'pgvector';` |
| **Extended Data Types** | New data types introduced (e.g., `vector`, `box`).                                               | `SELECT * FROM pg_type WHERE typname ~ '^vector$';` |
| **Extended Functions** | Functions added by the extension (e.g., `vector_cosine_similarity()`).                          | `SELECT * FROM pg_proc WHERE pronamespace::regnamespace = 'pgvector';` |
| **Extension Metadata** | Schema details (version, installed_by, installed_version).                                     | `SELECT * FROM pg_extension WHERE extname = 'pgvector';` |

---

## **Query Examples**

### **1. Check Extension Availability**
```sql
-- Check if an extension is available for installation.
SELECT * FROM pg_available_extensions WHERE name = 'pgvector';

-- Check if an extension is installed.
SELECT * FROM pg_extension WHERE extname = 'pgvector';
```

### **2. Install an Extension**
```sql
-- Basic installation (requires superuser privileges).
CREATE EXTENSION IF NOT EXISTS pgvector;

-- Install with specific version (if supported).
CREATE EXTENSION pgvector FROM 'C:\path\to\pgvector-0.6.0.sql';
```

### **3. Verify Dependencies**
```sql
-- Check if pgvector depends on spatial extensions (e.g., postgis).
SELECT * FROM pg_extension_depends WHERE extname = 'pgvector';
```

### **4. Query Extended Types**
```sql
-- List all new types added by pgvector.
SELECT typname, typarray
FROM pg_type
WHERE typnamespace = (
    SELECT oid FROM pg_namespace
    WHERE nspname = 'pgvector'
);
```

### **5. Test Extension Usage**
```sql
-- Verify a vector function exists and is callable.
SELECT exists (
    SELECT 1 FROM pg_proc
    WHERE proname = 'vector_cosine_similarity'
    AND pronamespace = 'pgvector'::regnamespace
);

-- Example query using a vector column.
SELECT id, text, vector_cosine_similarity(
    vector, '[0.1, 0.2, 0.3]'
) AS similarity
FROM documents
ORDER BY similarity DESC;
```

### **6. Handle Rollback (Safe Drop)**
```sql
-- Check constraints before dropping to avoid errors.
DO $$
DECLARE
    missing_constraints INT;
BEGIN
    -- Count constraints referencing extended types (e.g., vector).
    SELECT count(*) INTO missing_constraints
    FROM pg_constraint
    WHERE conrelid = 'documents'::regclass
    AND confrelid = (
        SELECT oid FROM pg_class
        WHERE relname = 'vector'
    );

    IF missing_constraints > 0 THEN
        RAISE EXCEPTION 'Cannot drop extension: dependencies exist.';
    ELSE
        DROP EXTENSION IF EXISTS pgvector CASCADE;
    END IF;
END $$;
```

---

## **Advanced Query: Dynamic Extension Check Script**
```sql
-- Script to validate all required extensions before query execution.
DO $$
DECLARE
    missing_extensions TEXT[];
    extension_list TEXT[] := ARRAY['pgvector', 'postgis'];
BEGIN
    -- Check each extension in the list.
    FOR ext IN SELECT unnest(extension_list) AS ext_name FROM (VALUES(NULL)) AS t LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_extension
            WHERE extname = ext.ext_name
        ) THEN
            missing_extensions := array_append(missing_extensions, ext.ext_name);
        END IF;
    END LOOP;

    IF missing_extensions IS NOT NULL THEN
        RAISE EXCEPTION 'Missing extensions: %', missing_extensions;
    END IF;

    -- Proceed with application logic.
    RAISE NOTICE 'All extensions validated.';
END $$;
```

---

## **Related Patterns**

1. **[Dependency Injection Pattern]**
   - Similar to extension dependencies, this pattern ensures external libraries are loaded before use. Applies to application-level dependencies (e.g., Python modules).

2. **[Schema Migration Pattern]**
   - Extensions modify schemas; pair with migration tools (e.g., Alembic, Flyway) to track changes. Example:
     ```sql
     -- Alembic-style migration for pgvector extension.
     CREATE TABLE IF NOT EXISTS documents (
         id SERIAL PRIMARY KEY,
         text TEXT,
         embedding vector(4)  -- New type from pgvector
     );
     ```

3. **[Feature Toggle Pattern]**
   - Use feature flags to enable/disable extensions in production (e.g., toggle `pgvector` for A/B testing).

4. **[Error Handling Pattern for Extensions]**
   - Catch extension-related errors gracefully:
     ```sql
     BEGIN;
         CREATE EXTENSION pgvector;
         -- Application queries here.
     EXCEPTION WHEN others THEN
         RAISE NOTICE 'Extension error: %', SQLERRM;
         -- Fallback logic.
     END;
     ```

5. **[Configuration Pattern for Extensions]**
   - Store extension requirements in config files (e.g., `postgres.conf` or environment variables) and validate at startup:
     ```json
     {
       "extensions": ["pgvector", "postgis"],
       "required_roles": ["app_user"]
     }
     ```