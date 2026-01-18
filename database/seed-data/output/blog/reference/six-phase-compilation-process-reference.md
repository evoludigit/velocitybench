# **[Pattern] Six-Phase Compilation Pipeline**
*Reference Guide for Structured Data-to-Artifact Compilation*

---

## **Overview**
This pattern defines a **six-phase compilation pipeline** that standardizes the process of converting high-level data definitions (schemas, models, or queries) into low-level artifacts (e.g., executable DDL, query plans, or service contracts). Each phase introduces constraints while incrementally refining the input until a validated, optimized output is generated. This approach ensures **modularity** (each phase can be extended or swapped independently), **debuggability** (mid-process artifacts are inspectable), and **performance** (optimizations are applied systematically).

The pipeline is **not linear**: feedback loops between phases (e.g., optimization may trigger re-binding) are common, though the primary sequence is:
**Parse → Bind → Filter → Validate → Optimize → Emit**.

---

## **Schema Reference: Six-Phase Pipeline**

| **Phase**          | **Input**                          | **Output**                          | **Key Process**                                                                 | **Error Conditions**                          | **Tools/Abstractions**                     |
|--------------------|------------------------------------|-------------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|-------------------------------------------|
| **1. Parse**       | Raw data definition (JSON/SQL)     | Abstract Syntax Tree (AST)          | Lexical analysis, parsing into a structured AST with unambiguous grammar.        | Syntax errors, unresolved references.        | Parser combinators, ANTLR, PEG.js.         |
| **2. Bind**        | AST + Type Definitions             | Bound AST (types resolved)           | Maps AST nodes to concrete database/table types, schemas, or external systems. | Type mismatches, missing schemas.             | Symbol tables, dependency injection.       |
| **3. Filter**      | Bound AST                          | Filtered AST (WHERE clauses added)   | Infers/expands WHERE clauses from constraints (e.g., "only active users").     | Incomplete constraints, circular dependencies. | Constraint solvers, rule engines.          |
| **4. Validate**    | Filtered AST                       | Validated AST + Checks Report       | Static analysis for integrity (e.g., "no NULLs in PKs", "foreign keys exist"). | Schema violations, logical contradictions.  | Property-based testing, Linters.           |
| **5. Optimize**    | Validated AST                      | Optimized AST                        | Rewrites queries/plans (e.g., join ordering, predicate pushdown) for performance. | Optimization failures (e.g., cost model errors). | Query recompiler, cost analyzers.         |
| **6. Emit**        | Optimized AST                      | Artifacts (DDL, PL/pgSQL, API specs)| Translates AST into target format (e.g., SQL, GraphQL, REST contracts).       | Unsupported syntax, artifact generation errors.| Template engines, codegen tools.            |

---

## **Key Implementation Details**
### **1. Phase Interdependencies**
- **Feedback Loops**:
  - Phase 5 (Optimize) may trigger Phase 2 (Bind) if a type change improves cost.
  - Phase 3 (Filter) can fail mid-validation if constraints conflict (requiring re-binding).
- **Abort Conditions**:
  Any critical error in Phase 1–4 halts compilation; Phase 6 errors may require retrying prior phases.

### **2. Phase-Specific Optimizations**
- **Binding (Phase 2)**:
  Use **lazy resolution** for external dependencies (e.g., deferred foreign key checks until Phase 4).
  Example: Bind to a "virtual" schema until validation confirms its existence.
- **Filtering (Phase 3)**:
  Prefer **rule-based expansion** over runtime filtering (e.g., hardcode `WHERE is_active = true` if inferred).
- **Optimization (Phase 5)**:
  Cache rewritten ASTs for identical inputs (e.g., "SELECT * FROM users" → "SELECT id, name FROM users").

### **3. Error Handling**
- **Phase-Specific Errors**:
  - **Parse**: `SyntaxError` with line/column pointers.
  - **Bind**: `TypeMismatchError` with suggested corrections.
  - **Validate**: `IntegrityViolation` with affected constraints.
- **Recovery**:
  Provide **fallback strategies** (e.g., skip optimization, emit fallback SQL).

### **4. Tooling Integration**
| **Tool/Framework**       | **Role**                                                                 |
|--------------------------|--------------------------------------------------------------------------|
| **ANTLR**                | Generate parsers for input grammars (Phase 1).                         |
| **SQL Compiler (e.g., Dolt, Calcite)** | Template for Phases 2–6 in query contexts.                         |
| **Kusto Query Language** | Phase 5 optimization for time-series data.                                  |
| **OpenAPI Generator**    | Phase 6 for API contracts.                                              |

---

## **Query Examples**
### **Example 1: SQL DDL Compilation**
**Input (Phase 1 AST):**
```json
{
  "type": "CREATE_TABLE",
  "name": "users",
  "columns": [
    {"name": "id", "type": "INT", "constraint": "PRIMARY_KEY"},
    {"name": "email", "type": "VARCHAR(255)", "constraint": "UNIQUE"}
  ]
}
```

**Phases 2–6 Output:**
1. **Bind**: Resolves `INT` → `pg_catalog.integer`, `VARCHAR` → `text`.
2. **Filter**: No constraints → no changes.
3. **Validate**: Checks `PRIMARY_KEY` on `id`; passes.
4. **Optimize**: Rewrites `VARCHAR` to `TEXT` (PostgreSQL alias).
5. **Emit**:
   ```sql
   CREATE TABLE users (
     id SERIAL PRIMARY KEY,
     email TEXT UNIQUE
   );
   ```

### **Example 2: GraphQL Schema Compilation**
**Input (Phase 1):**
```graphql
type User @model {
  id: ID!
  email: String! @unique
  posts: [Post] @belongsToMany
}
```

**Phases 2–6 Output:**
1. **Bind**: Maps `@model` → database table, `@unique` → constraint.
2. **Filter**: Expands `posts` association into JOIN conditions.
3. **Validate**: Confirms `email` is non-nullable.
4. **Optimize**: Adds index hints for `@unique`.
5. **Emit**:
   ```sql
   CREATE TABLE users (
     id SERIAL PRIMARY KEY,
     email TEXT UNIQUE,
     posts_id INT[]  -- Array for many-to-many
   );
   ```

---

## **Related Patterns**
1. **Incremental Compilation**
   - *Use Case*: Reuse Phase 2–5 outputs when input changes slightly (e.g., adding a column).
   - *Example*: Track AST deltas between compiles to skip redundant phases.

2. **Canonical Intermediate Representation (CIR)**
   - *Use Case*: Replace Phase 1–4 with a single "compilation to CIR" step, then optimize/emit from CIR.
   - *Example*: Calcite’s logical/physical plan phases.

3. **Phase-Specific Extensibility**
   - *Use Case*: Plugin architecture for custom phase implementations (e.g., Phase 3 for domain-specific constraints).
   - *Example*: Extend Phase 2 to bind to a document database.

4. **Artifact Versioning**
   - *Use Case*: Track compilation artifacts by input schema version.
   - *Example*: Store Phase 6 outputs in a registry like [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

5. **Multi-Pass Optimization**
   - *Use Case*: Combine Phase 5 with iterative refinement (e.g., machine learning-driven query plans).
   - *Example*: Use a cost-based optimizer like [Clover](https://github.com/facebookincubator/clover).

---
## **Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Problem**                                                                 | **Mitigation**                                  |
|---------------------------------|------------------------------------------------------------------------------|-------------------------------------------------|
| **Monolithic Compiler**         | All phases in one function; hard to debug/modify.                          | Modularize phases as separate components.      |
| **Skipping Validation**         | Phases 3–4 bypassed for "performance"; silent failures.                      | Enforce validation unless explicitly disabled.  |
| **Over-Optimizing Early**       | Phase 5 runs on unvalidated input; wastes effort.                           | Validate before optimizing.                   |
| **Tight Coupling to Phases**    | Phase X depends directly on Phase Y’s implementation.                       | Use well-defined interfaces (e.g., AST schema). |

---
## **Further Reading**
- [Calcite: A SQL Query Compiler](https://calcite.apache.org/)
- [SQL Compiler Design Patterns](https://www.oreilly.com/library/view/sql-compiler-design/9781491942453/)
- [GraphQL Schema Stitching](https://www.apollographql.com/docs/apollo-server/schema/stitching/) (for multi-phase GraphQL compilation).