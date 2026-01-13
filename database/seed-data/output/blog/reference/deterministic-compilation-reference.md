# **[Pattern] Deterministic Compilation: Reference Guide**

---

## **Overview**
Deterministic compilation ensures that the compilation process generates **identical output artifacts** for a given input, regardless of environment or runtime conditions. In this pattern, the **CompiledSchema** (or similar artifact) is a direct deterministic function of its input schema, configuration, and dependencies. This guarantees **reproducible builds**, **cacheability**, and **predictable deployment results**, making it critical for scalable, CI/CD-friendly applications.

Key benefits include:
- **Cache optimizations** (e.g., artifact reuse in build pipelines).
- **Predictable behavior** (identical schemas across different deploys).
- **Fault tolerance** (replayability of builds).

---
## **Schema Reference**
The following table defines the core inputs and outputs of deterministic compilation.

| **Field**               | **Type**       | **Description**                                                                 | **Example**                                                                 |
|-------------------------|---------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Input Schema**        | `SchemaSpec`  | The input schema definition (e.g., OpenAPI, Protobuf, or GraphQL schema).      | `{ "type": "object", "properties": { "name": { "type": "string" } } }`       |
| **Compiler Version**    | `string`      | Version of the compiler (must remain fixed for reproducibility).               | `"compiler-v1.2.3"`                                                          |
| **Compiler Config**     | `Config`      | Compilation settings (e.g., language target, optimizations, strictness).       | `{"target": "javascript", "optimize": true, "strict": true}`               |
| **Dependencies**        | `Dependency[]`| External libraries or schema definitions used in compilation.                 | `[{ "name": "@myorg/utils", "version": "1.0.0" }]`                           |
| **Output Artifact**     | `CompiledSchema` | The compiled, deterministic output (e.g., generated code, schema stubs).     | `{ "generatedCode": "module.exports = { ... };", "schemaHash": "abc123" }` |

### **Key Properties of Deterministic Outputs**
1. **Immutability**: The `CompiledSchema` hash or checksum must **never** change for the same inputs.
2. **Versioning**: Compiler versions and dependency versions **must** be pinned to avoid unintended changes.
3. **Idempotency**: Recompiling the same inputs yields **exactly the same bytes**.

---

## **Implementation Details**
To achieve deterministic compilation, follow these guidelines:

### **1. Input Normalization**
- **Flatten schemas**: Resolve all imports/extensions recursively into a single normalized input.
- **Sort dependencies**: Use a consistent order (e.g., lexicographical) to avoid dependency-order inconsistencies.
- **Canonicalize config**: Convert config objects to a standardized string representation (e.g., JSON with sorted keys).

### **2. Compiler Execution**
- **Fixed seed/prng**: If randomness is used (e.g., for code generation), seed it deterministically (e.g., from input hashes).
- **No runtime side effects**: Ensure the compiler does not query external services (e.g., timestamps, network calls).
- **Hash-based outputs**: Use cryptographic hashes (SHA-256) of inputs to derive deterministic outputs.

### **3. Artifact Storage**
- **Immutable storage**: Store compiled artifacts in a content-addressable system (e.g., Docker layers, Git LFS, or IPFS).
- **Cache headers**: Use `ETag` or `Last-Modified` to validate cache hits during deployments.

---
## **Query Examples**
### **Example 1: Compiling a Schema with Fixed Dependencies**
```bash
# Input: schema.json + pinned dependencies
npx deterministic-compiler \
  --schema schema.json \
  --config target=javascript,optimize=true \
  --dependencies "@myorg/utils@1.0.0,protbuf>=3.20.0" \
  --output compiled.js
```
**Output**: `compiled.js` with a hash embedded in its metadata (e.g., `//# Compiled from schema@abc123`).

### **Example 2: Reusing a Cached Compilation**
```bash
# Reuse the cached artifact if inputs haven’t changed
if [ "$(sha256sum schema.json dependencies.txt)" == "$CACHE_HASH" ]; then
  cp cached/compiled.js .
else
  npx deterministic-compiler --inputs schema.json --cache-dir ./cached
fi
```

### **Example 3: Schema Comparison for Determinism**
```javascript
// Verify two compiled schemas are identical
const hash1 = crypto.createHash("sha256").update(schema1).digest("hex");
const hash2 = crypto.createHash("sha256").update(schema2).digest("hex");
if (hash1 !== hash2) throw new Error("Non-deterministic compilation detected!");
```

---
## **Validation Checks**
To enforce determinism, implement these checks:
1. **Pre-Compilation**:
   ```bash
   # Ensure inputs are stable before compilation
   git diff --cached --exit-code schema.json dependencies.txt
   ```
2. **Post-Compilation**:
   ```javascript
   // Compare current output hash with a known good hash
   const artifactHash = await fs.promises.readFile("compiled.js", "utf-8");
   if (!artifactHash.startsWith("//# Compiled from schema@abc123")) {
     throw new Error("Artifact mismatch!");
   }
   ```

---
## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Interaction**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **[Idempotent Deployments]**     | Ensures deployments can be safely retried without unintended side effects.      | Deterministic compilation guarantees idempotent artifacts for deployment.     |
| **[Dependency Canary Testing]**  | Gradually rolls out new dependency versions to detect breaking changes early.  | Requires deterministic outputs to compare versions accurately.                |
| **[Schema Evolution Control]**   | Manages backward/forward compatibility of schema changes.                      | Uses deterministic outputs to validate compatibility before deployment.        |
| **[Build Caching]**              | Reuses intermediate build artifacts to speed up pipelines.                    | Compiled schemas are ideal cache candidates due to determinism.                |

---
## **Troubleshooting**
| **Issue**                          | **Cause**                                      | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------|------------------------------------------------------------------------------|
| **Artifact hash changes**          | Unpinned dependencies or compiler version.      | Pin all versions in the compiler config.                                    |
| **Non-deterministic codegen**      | Random seed in compiler or runtime.             | Use a fixed seed derived from input hashes.                                 |
| **Cache misses**                   | Inputs changed but not detected.               | Implement robust input hashing and cache validation.                         |

---
## **Tools & Libraries**
- **[Compiler SDKs]**: Use libraries like `ts-morph` (TypeScript) or `protobuf-compiler` (Protobuf) with deterministic flags.
- **[Build Systems]**: Integrate with `bazel`, `npm`, or `Docker` for cache-friendly compilation.
- **[Schema Tools]**:
  - [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator) (with `--skip-scripts`).
  - [GraphQL Codegen](https://graphql-code-generator.com/) (use `--no-watch` for deterministic runs).

---
## **Best Practices**
1. **Document Inputs**: Clearly list all inputs (schema, deps, compiler version) in your artifact metadata.
2. **Automate Validation**: Add CI checks to verify determinism (e.g., compare hashes of repeated builds).
3. **Isolate Compilation**: Run compilers in clean environments (e.g., Docker containers) to avoid polluting state.
4. **Monitor Changes**: Use tools like `git diff` or `jq` to detect schema drifts before they affect production.