# **[Pattern] Snapshot Testing Reference Guide**

---

## **Overview**
**Snapshot Testing** is a developer-friendly testing pattern designed to maintain consistency between a schema and its compiled runtime representation (e.g., generated code, API contract, or serialized structure). It ensures that changes to the schema (e.g., JSON Schema, OpenAPI, Protobuf, or GraphQL SDL) do not introduce unintended structural changes, such as missing fields, deprecated fields, or type mismatches. This pattern is particularly useful in large-scale systems where schema definitions and their implementations are decoupled (e.g., microservices, code generation, or API gateways).

Snapshot Testing works by capturing a "golden" state (snapshot) of the compiled schema at a given point in time and automatically verifying that future compilations produce the same structure. Drifts between snapshots trigger warnings or failures, alerting developers to potential breaking changes.

---

## **Schema Reference**
The following tables define key elements of the **Snapshot Testing** pattern, including schema types, configuration options, and common use cases.

| **Category**               | **Key Concept**                          | **Description**                                                                                     | **Example Values**                                                                                     |
|----------------------------|------------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Core Components**        | **Source Schema**                        | The original schema definition (e.g., JSON Schema, OpenAPI Spec, Protobuf `.proto`).                | `schema/openapi.yaml`, `src/models/schema.json`                                                      |
|                            | **Compiled Output**                      | The generated artifacts from the schema (e.g., TypeScript types, Go structs, OpenAPI clients).      | `dist/generated/api.ts`, `protobuf/generated/pb.go`                                                 |
|                            | **Snapshot File**                        | A serialized record of the compiled schema structure (e.g., JSON, YAML, or binary format).         | `snapshots/api_schema.snapshot.json`                                                              |
| **Configuration**          | `snapshotAlgorithm`                     | The method used to compare snapshots (e.g., shallow equality, structural diff, or semantic checks). | `"shallow"`, `"deep"`, `"semantic"`                                                                  |
|                            | `snapshotOutputPath`                    | Directory where snapshot files are stored.                                                          | `./snapshots/`                                                                                      |
|                            | `ignoreFields`                          | Fields in the schema that should be excluded from comparison (e.g., timestamps, IDs).              | `["metadata.createdAt", "metadata.updatedAt"]`                                                     |
|                            | `allowNewFields`                        | Whether to permit additional fields not present in the snapshot.                                     | `true`/`false`                                                                                     |
| **Comparison Modes**       | `strictMode`                            | If `true`, any deviation (even minor) triggers a failure; if `false`, only major changes fail.     | `true`/`false`                                                                                     |
|                            | `warnOnChange`                          | Logs changes as warnings instead of failing the test.                                                 | `true`/`false`                                                                                     |
| **Tooling Integration**    | `generatorCommand`                      | The command to run the schema generator (e.g., `openapi-generator`, `protobuf-compiler`).           | `npx openapi-generator-cli generate -i ./schema.yaml -g typescript-axios`                          |
|                            | `snapshotCleanup`                       | Whether to delete old snapshots after comparison.                                                    | `true`/`false`                                                                                     |
| **Metadata**               | `snapshotVersion`                       | A version tag (e.g., semantic version) to track schema evolution.                                  | `v1.2.0`                                                                                            |
|                            | `snapshotAuthor`                        | The developer’s identifier (e.g., Git username) responsible for the snapshot.                        | `"johndoe"`                                                                                         |

---

## **Implementation Details**
### **Key Concepts**
1. **Schema Compilation**:
   Schema definitions are compiled into runtime artifacts (e.g., code, API clients, or protobuf messages) using tools like:
   - **OpenAPI/Swagger**: `openapi-generator`, `@openapitools/openapi-generator-cli`.
   - **Protobuf**: `protoc` compiler.
   - **JSON Schema**: `json-schema-to-typescript`, `ajv-cli`.
   - **GraphQL**: `graphql-codegen`.

2. **Snapshot Capture**:
   After compilation, the structure of the generated artifacts is serialized into a snapshot file. The exact format depends on the tooling:
   - **Structural Snapshots**: Capture field names, types, and relationships (e.g., JSON/YAML representations of the schema graph).
   - **Binary Snapshots**: Use checksums or hashes of generated files for faster comparison (e.g., `sha256` of `.ts` or `.go` files).

3. **Comparison Logic**:
   The snapshot is compared against the current compiled output using one of the following strategies:
   - **Shallow Comparison**: Checks for exact file equality (e.g., `fs.readFileSync` in Node.js).
   - **Deep Comparison**: Recursively validates schema structure (e.g., using `deep-equal` or custom parsers).
   - **Semantic Comparison**: Focuses on logical equivalence (e.g., type compatibility, field presence) rather than exact syntax.

4. **Change Handling**:
   - **Fail Fast**: Default behavior; any drift causes the test to fail.
   - **Warn Only**: Logs changes but allows the build to continue (useful for non-critical updates).
   - **Auto-Update**: Overwrites the snapshot with the new state (useful in CI/CD pipelines for controlled updates).

5. **Tooling Workflow**:
   ```
   1. Compile schema → generated artifacts
   2. Serialize artifacts into snapshot
   3. Compare snapshot vs. previous snapshot
   4. Emit result (pass/fail/warn)
   ```

---

## **Query Examples**
### **1. Basic Snapshot Test (TypeScript)**
This example uses a custom script to compare a generated TypeScript file against a snapshot.

```typescript
// snapshotTest.ts
import fs from 'fs';
import { parse } from '@babel/parser';
import traverse from '@babel/traverse';
import { generate } from '@babel/generator';

const compileSchema = () => {
  // Simulate running `openapi-generator-cli` or similar
  return fs.readFileSync('dist/generated/api.ts', 'utf-8');
};

const generateSnapshot = (code: string) => {
  const ast = parse(code, { sourceType: 'module' });
  const fields: Record<string, any> = {};

  traverse(ast, {
    ClassDeclaration(path) {
      if (path.node.id?.name === 'ApiClient') {
        fields[path.node.id.name] = [];
        path.node.body.body.forEach((stmt) => {
          if (stmt.type === 'VariableDeclaration') {
            fields[path.node.id.name].push(
              stmt.declarations[0].id.name
            );
          }
        });
      }
    },
  });

  return JSON.stringify(fields, null, 2);
};

const compareSnapshots = (currentSnapshot: string, previousSnapshot: string) => {
  const current = JSON.parse(currentSnapshot);
  const previous = JSON.parse(previousSnapshot);

  // Simple deep comparison (extend as needed)
  const keys = new Set([...Object.keys(current), ...Object.keys(previous)]);
  for (const key of keys) {
    if (current[key] !== previous[key]) {
      throw new Error(`Mismatch in ${key}: ${JSON.stringify(current[key])} vs ${JSON.stringify(previous[key])}`);
    }
  }
};

const execute = async () => {
  const currentCode = compileSchema();
  const currentSnapshot = generateSnapshot(currentCode);
  const previousSnapshot = fs.readFileSync('snapshots/api.ts.snapshot', 'utf-8');

  // Overwrite snapshot in CI/CD (e.g., GitHub Actions)
  if (process.env.UPDATE_SNAPSHOT) {
    fs.writeFileSync('snapshots/api.ts.snapshot', currentSnapshot);
    return { status: 'snapshot_updated' };
  }

  try {
    compareSnapshots(currentSnapshot, previousSnapshot);
    return { status: 'pass' };
  } catch (err) {
    return { status: 'fail', error: err.message };
  }
};

execute();
```

---

### **2. OpenAPI Snapshot Test (Bash + `jq`)**
Use `jq` to compare OpenAPI JSON structure against a snapshot.

```bash
#!/bin/bash
# generate_and_compare.sh

# Step 1: Generate OpenAPI client (e.g., using openapi-generator)
npx openapi-generator-cli generate \
  -i ./schema.yaml \
  -g typescript-axios \
  -o ./dist/generated

# Step 2: Extract schema structure (e.g., paths, operations)
SCHEMA_STRUCTURE=$(jq '.paths | keys[] as $path | {path: $path, methods: .[$path] | keys}' ./dist/generated/openapi.json)

# Step 3: Compare against snapshot
PREV_SNAPSHOT=$(cat snapshots/openapi_structure.snapshot)
if [ "$SCHEMA_STRUCTURE" != "$PREV_SNAPSHOT" ]; then
  echo "❌ Schema structure changed!"
  echo "Current:  $SCHEMA_STRUCTURE"
  echo "Previous: $PREV_SNAPSHOT"
  exit 1
fi

# Step 4: Overwrite snapshot in CI (if UPDATE_SNAPSHOT=1)
if [ "$UPDATE_SNAPSHOT" = "1" ]; then
  echo "$SCHEMA_STRUCTURE" > snapshots/openapi_structure.snapshot
  echo "✅ Snapshot updated."
fi
```

---

### **3. Protobuf Snapshot Test (Python)**
Use `protobuf` Python library to compare `.proto` definitions.

```python
# snapshot_protobuf.py
import os
from google.protobuf import descriptor_pool, descriptor_pb2
from google.protobuf.compiler.importer import Importer

def generate_proto_snapshot(proto_file: str) -> dict:
    """Generate a snapshot of a protobuf schema."""
    importer = Importer([os.path.dirname(proto_file)])
    file_descriptor = importer.Import(proto_file)
    pool = descriptor_pool.DescriptorPool()
    pool.Add(file_descriptor)

    snapshot = {}
    for message in pool.FindFileByName(proto_file).message_types_by_name.values():
        snapshot[message.name] = {
            "fields": [
                (field.name, field.type.name)
                for field in message.fields
            ]
        }
    return snapshot

def compare_snapshots(current: dict, previous: dict) -> bool:
    """Compare two protobuf snapshots."""
    for name, fields in current.items():
        if name not in previous:
            return False
        if len(fields["fields"]) != len(previous[name]["fields"]):
            return False
        for field in fields["fields"]:
            if field not in previous[name]["fields"]:
                return False
    return True

def main():
    proto_file = "src/api/proto/api.proto"
    current_snapshot = generate_proto_snapshot(proto_file)

    # Overwrite snapshot in CI
    if os.environ.get("UPDATE_SNAPSHOT"):
        import json
        with open("snapshots/proto.snapshot", "w") as f:
            json.dump(current_snapshot, f)
        print("Snapshot updated.")
        return

    try:
        with open("snapshots/proto.snapshot", "r") as f:
            previous_snapshot = json.load(f)
        if not compare_snapshots(current_snapshot, previous_snapshot):
            raise ValueError("Snapshot mismatch!")
        print("✅ Protobuf schema unchanged.")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
```

---

## **Related Patterns**
Snapshot Testing is often combined with or inspired by the following patterns:

| **Pattern**               | **Description**                                                                 | **Use Case**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Schema Registry**       | Centralized storage for schema definitions (e.g., Confluent Schema Registry).   | Versioning and governance of schemas across services.                                           |
| **Contract Testing**      | Tests interactions between services based on their API contracts.                  | Ensuring microservices adhere to their agreed-upon interfaces.                                   |
| **Golden Master Testing** | Captures an expected "golden" state of data for validation.                      | Data validation pipelines (e.g., ensuring ETL outputs match expectations).                       |
| **Differential Testing**  | Compares outputs across different versions of the same schema.                  | Backward-compatibility checks for schema evolution.                                               |
| **Canonical Data Model**  | Defines a normalized representation of data across systems.                       | Aligning schemas in heterogeneous environments (e.g., SQL → NoSQL).                            |
| **GitOps for Schemas**    | Manages schema definitions as code in version control.                         | Collaborative schema development with branching/merging (e.g., GitHub/GitLab).                |

---

## **Best Practices**
1. **Scope Snapshots**:
   - Snapshots should represent the "minimum viable" structure. Exclude volatile fields (e.g., timestamps, IDs) using `ignoreFields`.
   - Example: For OpenAPI, focus on `paths`, `operations`, and `parameters` rather than `servers` or `externalDocs`.

2. **Versioning**:
   - Tag snapshots with version numbers (e.g., `v1.2.0`) to track schema evolution.
   - Use semantic versioning to correlate snapshots with release cycles.

3. **CI/CD Integration**:
   - Run snapshot tests in CI pipelines with `failFast: true` for stability.
   - Allow snapshot updates only in controlled environments (e.g., `UPDATE_SNAPSHOT=1` in GitHub Actions).

4. **Tooling**:
   - Leverage existing tools:
     - **OpenAPI**: [`openapi-snapshot`](https://github.com/agilepal/openapi-snapshot) (Node.js).
     - **Protobuf**: Custom scripts using `protoc` and checksums.
     - **GraphQL**: [`graphql-codegen`](https://graphql-codegen.com/) + custom comparators.

5. **Documentation**:
   - Document why a snapshot was updated (e.g., Git commit message: `"Update snapshot: Added new /users endpoint"`).

6. **Performance**:
   - For large schemas, use incremental snapshots (only compare changed files) or binary diff tools like `xxdiff`.

---

## **Failure Scenarios and Mitigations**
| **Scenario**                          | **Cause**                              | **Mitigation**                                                                                     |
|---------------------------------------|----------------------------------------|---------------------------------------------------------------------------------------------------|
| False Positive (Non-Breaking Change)  | New optional field added.              | Use `allowNewFields: true` or whitelist ignored fields.                                           |
| False Negative (Semantic Change)     | Field renamed but logic unchanged.     | Use semantic comparison (e.g., check field *purpose* rather than *name*).                        |
| Performance Bottleneck               | Large schema with complex generics.    | Pre-filter snapshots or use binary hashing instead of full serialization.                        |
| Tooling Misconfiguration              | Wrong generator flags.                 | Validate snapshots against a known-good baseline in pre-commit hooks.                            |
| Data Leak (Sensitive Fields)         | Snapshot includes API keys/secrets.     | Exclude sensitive fields (e.g., `ignoreFields: ["auth.token"]`) or use a separate "public" snapshot.|

---

## **Example Workflow**
1. **Developer**:
   - Updates `schema/openapi.yaml` to add a `/v2/users` endpoint.
   - Commits the change with a note: `"feat: Add v2 users API"`.

2. **CI Pipeline**:
   - Runs `openapi-generator-cli` to compile the schema.
   - Compares the new snapshot against `snapshots/openapi_structure.snapshot`.
   - Finds a mismatch in `paths["/v2"]["get"]["parameters"]` and fails the build.

3. **Developer Response**:
   - Reviews the snapshot diff to confirm the change is intentional.
   - Updates the snapshot in the pipeline (if in a controlled branch) or reverts the change.

4. **Documentation Update**:
   - Updates `README.md` with the new endpoint documentation.

---
This guide provides a comprehensive reference for implementing **Snapshot Testing** to ensure schema consistency. Adjust the examples and schemas to fit your specific tooling and environment.