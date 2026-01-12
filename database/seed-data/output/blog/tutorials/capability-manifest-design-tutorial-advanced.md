```markdown
---
title: "Capability Manifest Design: Declarative Database Feature Support at Scale"
author: "Alex Carter"
date: "2023-11-15"
tags: ["database design", "SQL compilation", "API design", "compiler patterns"]
description: "Learn how to design a capability manifest system to declaratively define database feature support, enabling intelligent query compilation and optimization."
---

```markdown
# Capability Manifest Design: Declarative Database Feature Support at Scale

![Capability Manifest Architecture Diagram](https://via.placeholder.com/800x400?text=Capability+Manifest+System+Architecture)

---

## Introduction

As databases grow in complexity—supporting multi-model schemas, distributed operations, and specialized extensions—the challenge of tracking *feature support* across diverse backends becomes increasingly painful. Traditional approaches rely on hardcoded feature matrices, nested `if` statements, or repetitive conditional logic to determine which operators, functions, or extensions a database engine understands. However, these methods scale poorly, are brittle, and make it difficult to standardize how features are documented, versioned, or dynamically queried.

This is where the **Capability Manifest Design** pattern shines. Inspired by systems like FraiseQL (a modern SQL compiler), this pattern treats database feature support as **declarative, self-describing metadata**—stored in a structured manifest that can be programmatically queried, validated, and leveraged during compilation and optimization. By encapsulating feature definitions in a machine-readable format, you enable tools to:
- Dynamically discover supported operators (`JOIN`, `WINDOW`, `CTE`) and functions (`SUBSTR`, `JSON_EXTRACT`).
- Validate queries against capabilities before compilation.
- Optimize execution plans based on backend-specific strengths.
- Easily extend support for new features without rewriting logic.

In this tutorial, we’ll explore how to design, implement, and maintain a capability manifest system, complete with real-world tradeoffs and practical examples.

---

## The Problem: Hardcoded Feature Support Matrices

Imagine maintaining a SQL compiler or a database abstraction layer (e.g., a query planner) that needs to support multiple backends: PostgreSQL, MySQL, ClickHouse, and an experimental graph database. The naive approach might look like this:

### **Example 1: Hardcoded Feature Check**
```python
def supports_window_function(backend: str, query: str) -> bool:
    if backend == "postgres":
        return "OVER(" in query
    elif backend == "clickhouse":
        return "arrayJoin" not in query  # ClickHouse has limitations
    elif backend == "mysql":
        return False  # MySQL’s window functions are limited
    else:
        raise NotImplementedError(f"Unsupported backend: {backend}")
```

**Issues with this approach:**
1. **Brittle:** Adding a new backend or feature requires modifying this monstrosity.
2. **Hard to document:** Features are scattered across code, making it hard to know what’s supported where.
3. **No versioning:** Updates to feature support (e.g., MySQL now supports window functions in v8.0+) require manual code changes.
4. **No compiler-friendly metadata:** This isn’t structured for tools like AST walkers or optimizers to use.

### **Example 2: Nested Conditional Logic**
```python
def get_operator_support(backend: str, operator: str) -> bool:
    if operator == "JOIN":
        if backend == "postgres":
            return True
        elif backend == "mysql":
            return True
        elif backend == "clickhouse":
            return True
    elif operator == "WINDOW":
        if backend == "postgres" or backend == "clickhouse":
            return True
        else:
            return False
    # ... 50 more conditions
    raise ValueError(f"Unsupported operator: {operator}")
```

This quickly becomes **unmaintainable** as the feature set grows.

---

## The Solution: Capability Manifest Design

The capability manifest pattern solves these problems by **externalizing feature declarations** into a structured, versioned data format. The core idea is:
- **Declarative:** Define features (operators, functions, extensions) as metadata.
- **Backend-specific:** Each backend has its own manifest.
- **Machine-readable:** Compilers and tools can parse and query the manifest programmatically.
- **Versioned:** Supports per-version feature tracking (e.g., `JOIN` in MySQL 8.0+).

### **Key Components**
1. **Manifest Structure:** A JSON/YAML/Protobuf schema describing capabilities.
2. **Registry:** A centralized location (file, database, or cache) for manifests.
3. **Resolution Layer:** Logic to fetch and validate manifests at runtime.
4. **Compiler Integration:** Use manifests during query parsing, optimization, and codegen.

---

## Capability Manifest: Code Examples

### **1. Manifest Definition (JSON Example)**
Here’s how a manifest for PostgreSQL might look:

```json
{
  "$schema": "https://fraise.dev/manifest/v1",
  "name": "postgres",
  "version": "16",
  "operators": [
    {
      "name": "JOIN",
      "types": ["INNER", "LEFT", "RIGHT", "FULL"],
      "since": "9.0",
      "restrictions": [
        {
          "condition": "JOIN_USING",
          "supported": false,
          "reason": "JOIN USING is not optimized in this version"
        }
      ]
    },
    {
      "name": "WINDOW",
      "types": ["ROWS_BETWEEN", "RANGE_BETWEEN", "FRAME_BETWEEN"],
      "since": "9.4",
      "extensions": ["jsonb"]
    }
  ],
  "functions": [
    {
      "name": "SUBSTR",
      "args": [
        { "type": "text|bytea", "name": "string" },
        { "type": "integer", "name": "start" },
        { "type": "integer", "name": "length" }
      ],
      "since": "8.0"
    },
    {
      "name": "JSON_EXTRACT_PATH",
      "args": [{ "type": "jsonb", "name": "json" }, { "type": "text", "name": "path" }],
      "since": "9.5"
    }
  ],
  "extensions": [
    { "name": "unaccent", "since": "10.0" },
    { "name": "pg_trgm", "since": "9.5" }
  ]
}
```

### **2. Manifest Registry (Python Example)**
Store manifests in a directory or database, and provide a simple resolver:

```python
import json
from pathlib import Path
from typing import Dict, Optional

class ManifestRegistry:
    def __init__(self, manifest_dir: str = "manifests"):
        self.manifest_dir = Path(manifest_dir)

    def load_manifest(self, backend: str, version: str) -> Dict:
        """Load a manifest for a given backend and version."""
        path = self.manifest_dir / f"{backend}_{version}.json"
        if not path.exists():
            raise FileNotFoundError(f"Manifest for {backend} v{version} not found")
        with open(path, "r") as f:
            return json.load(f)

    def get_capability(
        self,
        backend: str,
        version: str,
        capability_type: str,
        name: str
    ) -> Optional[Dict]:
        """Check if a capability exists (e.g., operator/function)."""
        manifest = self.load_manifest(backend, version)
        if capability_type not in manifest:
            return None

        for item in manifest[capability_type]:
            if item["name"] == name:
                return item
        return None
```

### **3. Compiler Integration: Query Validation**
Use the manifest to validate queries before compilation:

```python
class QueryValidator:
    def __init__(self, manifest_registry: ManifestRegistry):
        self.manifest_registry = manifest_registry

    def validate_window_function(self, backend: str, version: str, query: str) -> bool:
        """Check if the backend supports WINDOW functions."""
        manifest = self.manifest_registry.load_manifest(backend, version)
        if "operators" not in manifest or "WINDOW" not in manifest["operators"]:
            return False

        window_func = manifest["operators"][0]  # Assuming first entry is WINDOW
        return window_func.get("since", "").startswith(version.split(".")[0])
```

### **4. Dynamic Code Generation**
Use manifests to generate backend-specific SQL:

```python
def generate_join_clause(backend: str, version: str, join_type: str) -> str:
    manifest = manifest_registry.load_manifest(backend, version)
    if join_type.upper() not in [op["types"] for op in manifest["operators"] if op["name"] == "JOIN"]:
        raise ValueError(f"{backend} v{version} does not support {join_type} joins")

    if backend == "clickhouse":
        return f"ARRAY JOIN {join_type.upper()} USING"
    elif backend == "postgres":
        return f"{join_type.upper()} JOIN"
    else:
        raise NotImplementedError(f"Join generation not implemented for {backend}")
```

---

## Implementation Guide

### **Step 1: Define Your Manifest Schema**
Start with a schema like the JSON example above. Key fields:
- `name`: Backend identifier (e.g., `postgres`).
- `version`: Semantic version (e.g., `16`).
- `operators`, `functions`, `extensions`: Arrays of capability objects.
- `since`: Minimum version supporting the feature.

**Pro Tip:** Use a tool like [JSON Schema](https://json-schema.org/) to validate manifests at load time.

### **Step 2: Populate the Registry**
Store manifests in a structured way:
- Option 1: Filesystem (e.g., `manifests/postgres_16.json`).
- Option 2: Database table (e.g., `capability_manifests` with `backend`, `version`, `data`).
- Option 3: Cache (e.g., Redis) for hot manifests.

### **Step 3: Integrate with Your Compiler**
Use the registry to:
1. **Validate queries:** Reject unsupported features early.
2. **Optimize plans:** Prioritize backends with stronger capabilities.
3. **Generate backend code:** Use manifests to select the right SQL dialect.

### **Step 4: Extend for Complex Scenarios**
- **Version ranges:** Support `since: ">=9.5"` or `since: "10.0-12.0"`.
- **Conditional features:** Add `requires: ["extension:jsonb"]`.
- **Performance metrics:** Include `performance_rating: "high"` for operators.

---

## Common Mistakes to Avoid

1. **Overcomplicating the Schema:**
   Start small. Your first manifest might only track `operators` and `functions`. Add complexity (e.g., `restrictions`) later.

2. **Ignoring Versioning:**
   Always track `since` versions. Without this, you’ll have no way to know if a feature was added in v10 but broken in v11.

3. **Hardcoding Defaults:**
   Avoid defaults like `supported: true` unless you’re absolutely sure. Always fetch from the manifest.

4. **Not Testing Edge Cases:**
   Test manifests for:
   - Missing capabilities (e.g., `GET` operator in PostgreSQL).
   - Version conflicts (e.g., `JOIN` in MySQL 5.7 vs. 8.0).
   - Malformed manifests (e.g., duplicate `name` fields).

5. **Tight Coupling to Backends:**
   Keep your compiler’s logic in terms of capabilities, not backend-specific quirks. This makes it easier to add new backends.

---

## Key Takeaways

- **Capability manifests replace hardcoded checks** with declarative metadata, making your system more maintainable.
- **They enable dynamic query validation**, catching unsupported features early.
- **Versioning is built-in**, making it easy to track feature support across database updates.
- **They empower optimizers**, as tools can compare capabilities to pick the best backend for a query.
- **Start small**, but design for extensibility. Your manifest schema should grow with your needs.

---

## Conclusion

The capability manifest design pattern is a powerful way to manage database feature support at scale. By treating capabilities as first-class metadata, you move from brittle conditional logic to a declarative, machine-readable system. This approach not only simplifies maintenance but also enables advanced optimizations and better tooling.

**Next Steps:**
1. Start with a minimal manifest schema (e.g., just `operators`).
2. Integrate it into your query planner’s validation phase.
3. Gradually add more capabilities (functions, extensions, performance metrics).
4. Experiment with runtime caching for better performance.

If you’re building a SQL compiler, query planner, or database abstraction layer, a capability manifest could be the missing piece that makes your system **scalable, maintainable, and intelligent**. Happy coding!

---
```

### **Appendix: Example Manifest for MySQL**
```json
{
  "$schema": "https://fraise.dev/manifest/v1",
  "name": "mysql",
  "version": "8.0",
  "operators": [
    {
      "name": "JOIN",
      "types": ["INNER", "LEFT", "RIGHT"],
      "since": "5.7",
      "restrictions": [
        {
          "condition": "JOIN USING",
          "supported": true,
          "since": "8.0"
        }
      ]
    },
    {
      "name": "WINDOW",
      "types": ["ROWS_BETWEEN"],
      "since": "8.0",
      "restrictions": [
        {
          "condition": "RANGE_BETWEEN",
          "supported": false,
          "reason": "Not implemented in 8.0"
        }
      ]
    }
  ],
  "functions": [
    {
      "name": "JSON_EXTRACT",
      "args": [
        { "type": "json", "name": "json" },
        { "type": "text", "name": "path" }
      ],
      "since": "5.7"
    }
  ]
}
```

### **Appendix: Performance Considerations**
- **Cache manifests aggressively** (e.g., 10-minute TTL) to avoid filesystem/database overhead.
- **Use a lightweight format** like JSON or Protocol Buffers for manifests.
- **Batch validate queries** if you’re processing many at once (e.g., in a batch job).