---
# **Debugging [Pattern]: Schema Parsing from Multiple Formats – A Troubleshooting Guide**
*For Python, YAML, GraphQL SDL, and TypeScript Schema Integration*

---

## **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms to isolate the issue:

✅ **Language-Specific Errors**
- Python: `SyntaxError`, `ModuleNotFoundError`, or `ImportError`.
- YAML: Parsing fails with `yaml.scanner.ScannerError` or `yaml.parser.ParserError`.
- GraphQL SDL: Invalid syntax in `.graphql`/`.gql` files (e.g., missing `type`, unclosed brackets).
- TypeScript: TSC errors (`Property 'xyz' does not exist on type 'Schema'`) or build failures.

✅ **Integration Failures**
- Schema loader/repo returns `null`/`undefined` or partial data.
- Parsed schemas mismatch across languages (e.g., Python’s `graphene` vs. TypeScript’s `graphql` types).
- External tooling (e.g., Apollo Studio, Prisma) rejects the schema due to structural mismatches.

✅ **Tooling/Dependency Issues**
- Version conflicts (e.g., `pyyaml@5.x` vs. `graphql@16.x`).
- Missing schema extensions (e.g., `@deprecated`, custom directives).
- Environment inconsistencies (e.g., Docker vs. local dev, CI/CD pipeline mismatches).

✅ **Data Corruption**
- Unexpected `None` values or missing fields in parsed schemas.
- Circular references in YAML/JSON that break serialization.
- GraphQL SDL with malformed directives (e.g., `extend type User @custom`).

✅ **Performance Bottlenecks**
- Slow parsing of large YAML/JSON files (e.g., >100MB).
- TypeScript compilation hangs on complex schemas.
- Python `ast.literal_eval` failing on deeply nested structures.

---

## **2. Common Issues and Fixes (with Code)**

### **Issue 1: Python Schema Parsing Errors**
**Symptoms:**
- `SyntaxError` on YAML/Python files.
- `AttributeError` on missing schema classes (e.g., `graphene.ObjectType`).

**Root Causes & Fixes:**
| Cause                          | Fix                                                                 | Example Code                                  |
|--------------------------------|---------------------------------------------------------------------|-----------------------------------------------|
| Invalid YAML indentation       | Use `ruamel.yaml` for strict parsing.                               | ```python from ruamel.yaml import YAML yaml = YAML(typ='safe') schema = yaml.load(open('schema.yaml')) ``` |
| GraphQL SDL syntax errors      | Validate with `graphql-language-service-server`.                    | ```bash npm install -g @graphql-language-service-server && gls validate schema.graphql ``` |
| Missing `graphene` imports     | Ensure `graphene` and `typing` modules are installed.               | ```python pip install graphene==3.0.0 typgql==0.4.0 ```                   |
| Dynamic imports fail           | Use `importlib` or `__import__` for runtime schema discovery.       | ```python import importlib schema_module = importlib.import_module('schema.graphql') ``` |

---

### **Issue 2: YAML Parsing Failures**
**Symptoms:**
- `yaml.scanner.ScannerError: while parsing a block mapping` in large files.
- Missing anchors/aliases (`&`, `*` references) break parsing.

**Fixes:**
```python
# Option 1: Strict YAML loading (Python's built-in)
import yaml
try:
    schema = yaml.safe_load(open('config.yaml'))
except yaml.YAMLError as e:
    print(f"YAML Error: {e}")
    # Fallback: Use ruamel for advanced features
    from ruamel.yaml import YAML
    yaml_parser = YAML(preserve_quotes=True, pure=True)
    schema = yaml_parser.load(open('config.yaml'))

# Option 2: Pre-process YAML with `yamlfix` (CLI)
# Install: pip install yamlfix
# Run: yamlfix --fix-indefinite-width-indent schema.yaml
```

---

### **Issue 3: GraphQL SDL Schema Mismatches**
**Symptoms:**
- TypeScript `graphql` parser rejects Python-generated SDL.
- Missing `Directives` or `InputTypes` in SDL.

**Fixes:**
```typescript
// Ensure consistent SDL structure (Python → TypeScript)
// Python (graphene):
from graphene import Schema, ObjectType, String
class User(ObjectType):
    name = String(required=True)
schema = Schema(query=User)

// Convert to TypeScript SDL:
const userType = `
  type User {
    name: String!
  }
`;
const schemaSDL = `
  type Query {
    user: User
  }
`;
```

**Key Checks:**
- **Directives:** Add `@deprecated`/`@custom` in SDL if used.
  ```graphql
  directive @custom(field: String!) on FIELD_DEFINITION
  type User @custom(field: "v1") {
    name: String!
  }
  ```
- **Extensions:** Use `graphql-tools` to merge SDL fragments:
  ```typescript
  import { mergeSDL } from '@graphql-tools/schema';
  const mergedSDL = mergeSDL([pythonSDL, typescriptSDL]);
  ```

---

### **Issue 4: TypeScript Schema Validation Failures**
**Symptoms:**
- TSC errors like `"Unknown type: 'MyCustomType'"`.
- Schema imports failing due to circular dependencies.

**Fixes:**
```typescript
// Fix 1: Use `graphql-codegen` for type-safe schemas
// 1. Install:
npm install @graphql-codegen/cli @graphql-codegen/typescript @graphql-codegen/typescript-resolvers
// 2. Generate types:
npx graphql-codegen --config codegen.ts
// codegen.ts:
const config = {
  schema: ["schema.graphql"],
  documents: ["src/**/*.ts"],
  generates: {
    "./src/gql/": {
      plugins: ["typescript", "typescript-resolvers"],
    },
  },
};

// Fix 2: Resolve circular dependencies with `module-alias`
// tsconfig.json:
{
  "compilerOptions": {
    "moduleResolution": "node16",
    "baseUrl": ".",
    "paths": {
      "@types/*": ["types/*"]
    }
  }
}
```

---

## **3. Debugging Tools and Techniques**
### **A. Logging and Validation**
- **Python/YAML:**
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  try:
      schema = yaml.safe_load(open('schema.yaml'))
  except Exception as e:
      logging.error(f"Parse failed: {e}", exc_info=True)
  ```
- **GraphQL SDL:**
  Use `graphql-validation-cli` for syntax checks:
  ```bash
  npx graphql-validation-cli schema.graphql --output json
  ```
- **TypeScript:**
  Enable strict mode in `tsconfig.json`:
  ```json
  {
    "compilerOptions": {
      "strict": true,
      "noImplicitAny": true
    }
  }
  ```

### **B. Schema Comparison Tools**
- **Diff Tools:**
  - `yq` (YAML/JSON): `yq eval-all '.[]' schema1.yaml > temp.json && yq eval-all '.[]' schema2.yaml > temp2.json && diff temp.json temp2.json`
  - **GraphQL:** [`graphql-schema-diff`](https://www.npmjs.com/package/graphql-schema-diff)
    ```bash
    npx graphql-schema-diff -s schema1.graphql -s schema2.graphql
    ```
- **Visualization:**
  - **GraphQL:** [`graphql-inspector`](https://github.com/prisma-labs/graphql-inspector) (for schema introspection).
  - **Python:** Use `graphene`’s `serialize()` to dump schemas as JSON.

### **C. Environment Debugging**
- **Docker:** Ensure all containers share the same schema versions:
  ```dockerfile
  COPY schema.graphql /app/schema.graphql
  RUN npm install --save graphql@16.6.0
  ```
- **CI/CD:** Add schema validation to workflows (e.g., GitHub Actions):
  ```yaml
  - name: Validate SDL
    run: npx graphql-validation-cli schema.graphql
  ```

---

## **4. Prevention Strategies**
### **A. Schema Standardization**
1. **Adopt a Unified Schema DSL:**
   - Use **GraphQL SDL** as the source of truth and transpile to other formats.
   - Example workflow:
     ```
     schema.graphql (SDL) → Python (graphene) → TypeScript (graphql) → YAML (config)
     ```
2. **Schema Linters:**
   - **GraphQL:** [`graphql-config`](https://www.graphql-code-generator.com/docs/plugins/linter) + [`graphql-tools`](https://www.apollographql.com/docs/apollo-server/schema/schema-tools/#validation).
   - **YAML:** [`yamllint`](https://github.com/adrienverge/yamllint).

### **B. Version Pinning**
- **Python (`requirements.txt`):**
  ```
  graphene==3.0.0
  pyyaml==6.0
  ```
- **TypeScript (`package.json`):**
  ```json
  {
    "dependencies": {
      "graphql": "^16.6.0",
      "@graphql-codegen/cli": "^3.2.2"
    }
  }
  ```
- **Lock Files:**
  - Use `poetry.lock` (Python) or `yarn.lock` (TypeScript) to avoid drift.

### **C. Automated Testing**
- **Python:**
  ```python
  # Test schema parsing in CI
  def test_schema_parsing():
      from pathlib import Path
      for file in Path("schemas").glob("*.yaml"):
          assert yaml.safe_load(file.open()) is not None
  ```
- **TypeScript:**
  ```typescript
  // Test SDL validity with Jest
  import { validateSDL } from 'graphql';
  test('SDL is valid', () => {
    const { errors } = validateSDL(schemaSDL);
    expect(errors).toBeUndefined();
  });
  ```

### **D. Schema Documentation**
- **Auto-generate docs from SDL:**
  - **GraphQL:** [`graphql-codegen`](https://www.npmjs.com/package/graphql-codegen) → Swagger/OpenAPI.
  - **Python:** [`sphinx-graphene`](https://github.com/graphql-python/sphinx-graphene).
- **Example `README.md` snippet:**
  ```markdown
  ## Schema
  ```graphql
  schema {
    query: Query
  }
  type Query {
    users: [User!]!
  }
  ```
  ```

### **E. Schema Migration Tools**
- **For breaking changes:**
  - **GraphQL:** [`graphql-migrate`](https://github.com/prisma-labs/graphql-migrate) (for SDL updates).
  - **Python → TypeScript:** Use [`graphql-to-python`](https://github.com/graphql-python/graphene) + [`graphql-codegen`](https://www.graphql-codegen.com/).

---

## **5. Quick Reference Table**
| **Issue**               | **Quick Fix**                          | **Tools**                                  |
|--------------------------|----------------------------------------|--------------------------------------------|
| YAML parsing errors      | Use `ruamel.yaml` or `yamlfix`         | `yamlfix`, `ruamel.yaml`                  |
| GraphQL SDL syntax       | Validate with `gls validate`            | `@graphql-language-service-server`         |
| Python `graphene` missing| Check `pip install graphene`            | `graphene` package                         |
| TypeScript TSC errors    | Run `npx graphql-codegen`              | `@graphql-codegen/cli`                     |
| Schema version conflicts | Pin versions in `requirements.txt`/`package.json` | `poetry.lock`, `yarn.lock`          |
| Circular YAML references | Pre-process with `yq`                  | `yq` (Miquel van Smoorenburg)               |

---

## **6. Final Checklist for Resolution**
Before closing an issue:
1. [ ] Reproduced the error in a clean environment.
2. [ ] Validated schema files with `gls validate`/`yamllint`.
3. [ ] Checked dependency versions (`pip list`, `npm ls`).
4. [ ] Compared parsed schemas with `graphql-schema-diff` or `yq`.
5. [ ] Tested in CI/CD pipeline (GitHub Actions, Jenkins, etc.).
6. [ ] Documented fixes in the codebase (e.g., `FIXED: YAML anchor parsing in v1.2`).

---
**Pro Tip:** For complex schemas, consider a **schema registry** (e.g., [Apollo Studio](https://www.apollographql.com/studio/)) to manage versions and avoid drift. For Python/TS integration, use [`graphql-python`](https://github.com/graphql-python/graphene) + [`graphql-codegen`](https://www.graphql-codegen.com/).