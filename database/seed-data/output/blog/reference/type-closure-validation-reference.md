# **[Pattern] Type Closure Validation – Reference Guide**

---

## **Overview**

Type Closure Validation ensures that all referenced types in a system form a **closed, acyclic, and constraint-compliant** graph. This pattern verifies:
- **Existence of referenced types** (no dangling references).
- **No circular dependencies** (ensures deterministic behavior).
- **Constraint satisfaction** (e.g., type hierarchies, inheritance, or interface implementations).

Common use cases include:
- Compile-time checks in programming languages (e.g., TypeScript, Rust).
- Schema validation in JSON/YAML-based configurations.
- Graph-based domain modeling (e.g., ontologies, API descriptions like OpenAPI).

Skipping this validation may lead to runtime errors (e.g., `UndefinedReferenceError`) or unintended behaviors (e.g., infinite recursion).

---

## **Key Concepts**

| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Type Node**         | A declared type (class, enum, interface, or primitive), represented as a unique identifier (e.g., `UserProfile`, `string`).                                                                          |
| **Type Edge**         | A relationship between types (e.g., inheritance, composition, or dependency) represented as a directed edge (e.g., `UserProfile → Address`).                                                     |
| **Type Closure**      | The transitive closure of a type’s dependencies (all types reachable from it, recursively).                                                                                                          |
| **Circular Dependency** | A cycle in the type graph (e.g., `A → B → A`), which violates deterministic validation.                                                                                                          |
| **Constraint**        | Rules enforced on relationships (e.g., "All derived types must implement `ILogger`").                                                                                                             |
| **Root Type**         | A type with no incoming edges (no dependencies).                                                                                                                                               |

---

## **Schema Reference**

### **1. Core Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "types": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string", "description": "Unique type identifier (e.g., 'User', 'Address')" },
          "kind": { "enum": ["class", "interface", "enum", "primitive"], "description": "Type classification" },
          "constraints": {
            "type": "object",
            "description": "Rules for this type (e.g., required interfaces)."
          }
        },
        "required": ["id", "kind"]
      }
    },
    "dependencies": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "source": { "type": "string", "description": "Dependent type ID" },
          "target": { "type": "string", "description": "Referenced type ID" },
          "relationship": {
            "type": "string",
            "enum": ["inherits", "implements", "composed_of", "uses"],
            "description": "Type of dependency"
          },
          "constraints": {
            "type": "object",
            "description": "Constraints on this relationship (e.g., 'must_be_final')."
          }
        },
        "required": ["source", "target", "relationship"]
      }
    }
  },
  "required": ["types", "dependencies"]
}
```

### **2. Validation Output Schema**
```json
{
  "type": "object",
  "properties": {
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": { "type": "string" },
          "message": { "type": "string" },
          "severity": { "enum": ["error", "warning"] }
        }
      }
    },
    "closure": {
      "type": "object",
      "description": "Transitive closure of all validated types."
    },
    "graph": {
      "type": "object",
      "description": "Visualizable graph of type relationships (e.g., DOT format)."
    }
  }
}
```

---

## **Implementation Steps**

### **1. Parse Input**
Convert type definitions into a **directed graph** ({`nodes`: [], `edges`: []}).
Example graph for:
```json
{
  "types": [{"id": "User", "kind": "class"}, {"id": "Address", "kind": "class"}],
  "dependencies": [
    {"source": "User", "target": "Address", "relationship": "composed_of"}
  ]
}
```
→ **Graph**:
```
User → Address
```

### **2. Validate Existence**
- Check all `target` IDs in `dependencies` exist in `types`.
- **Error**: `UnknownTypeError` if a target is missing.

### **3. Detect Cycles**
Use **Depth-First Search (DFS)** to detect cycles:
```python
visited = set()
stack = set()

def has_cycle(node):
    if node in stack:
        return True
    if node in visited:
        return False
    stack.add(node)
    for neighbor in graph[node]:
        if has_cycle(neighbor):
            return True
    stack.remove(node)
    visited.add(node)
    return False
```
- **Error**: `CircularDependencyError` (e.g., `User → Address → User`).

### **4. Enforce Constraints**
Apply rules per relationship:
| Relationship | Constraint Example                          | Violation Check                     |
|---------------|---------------------------------------------|-------------------------------------|
| `inherits`    | Child must not override `final` methods     | Check parent type’s `constraints`   |
| `implements`  | Type must implement all interface methods   | Verify method signatures            |
| `composed_of` |Referenced type must be a supported class   | Whitelist check                     |

### **5. Compute Closure**
For each root type, compute transitive dependencies (BFS/DFS):
```python
def compute_closure(node):
    closure = set()
    stack = [node]
    while stack:
        current = stack.pop()
        if current not in closure:
            closure.add(current)
            stack.extend(graph[current] - closure)
    return closure
```

### **6. Generate Output**
Return validated graph or errors:
```json
{
  "errors": [],
  "closure": {
    "User": ["User", "Address"],
    "Root": ["Root"]
  }
}
```

---

## **Query Examples**

### **1. Basic Validation**
**Input**:
```json
{
  "types": [
    {"id": "Logger", "kind": "interface"},
    {"id": "FileLogger", "kind": "class"}
  ],
  "dependencies": [
    {"source": "FileLogger", "target": "Logger", "relationship": "implements"}
  ]
}
```
**Output** (valid):
```json
{
  "errors": [],
  "closure": {
    "FileLogger": ["FileLogger", "Logger"],
    "Logger": ["Logger"]
  }
}
```

### **2. Circular Dependency**
**Input**:
```json
{
  "types": [
    {"id": "A", "kind": "class"},
    {"id": "B", "kind": "class"}
  ],
  "dependencies": [
    {"source": "A", "target": "B", "relationship": "uses"},
    {"source": "B", "target": "A", "relationship": "uses"}
  ]
}
```
**Output** (error):
```json
{
  "errors": [
    {
      "type": "B",
      "message": "Circular dependency detected: A → B → A",
      "severity": "error"
    }
  ]
}
```

### **3. Missing Type**
**Input**:
```json
{
  "types": [{"id": "User", "kind": "class"}],
  "dependencies": [
    {"source": "User", "target": "InvalidType", "relationship": "composed_of"}
  ]
}
```
**Output** (error):
```json
{
  "errors": [
    {
      "type": "InvalidType",
      "message": "Type 'InvalidType' not found in schema.",
      "severity": "error"
    }
  ]
}
```

### **4. Constraint Violation**
**Input**:
```json
{
  "types": [
    {"id": "FinalClass", "kind": "class", "constraints": {"final": true}},
    {"id": "Derived", "kind": "class"}
  ],
  "dependencies": [
    {"source": "Derived", "target": "FinalClass", "relationship": "inherits"}
  ]
}
```
**Output** (error):
```json
{
  "errors": [
    {
      "type": "Derived",
      "message": "Cannot inherit from 'FinalClass' (marked as final).",
      "severity": "error"
    }
  ]
}
```

---

## **Performance Considerations**

| Operation          | Complexity       | Optimization Notes                                                                 |
|--------------------|------------------|------------------------------------------------------------------------------------|
| Existence Check    | O(N)             | Use a hash set (`{type_id: type}`) for O(1) lookups.                               |
| Cycle Detection    | O(V + E)         | DFS with cycle tracking (early termination on first cycle found).                  |
| Closure Computation| O(V + E)         | Memoize results for overlapping subgraphs (e.g., shared dependencies).             |
| Constraint Check   | O(K) per edge    | Cache constraint evaluations (e.g., method signature checks).                       |

---

## **Related Patterns**

| Pattern                     | Description                                                                                     | When to Use                                      |
|-----------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Type Hierarchy Validation** | Validates inheritance chains (e.g., Liskov Substitution Principle).                           | When enforcing strict subclass contracts.       |
| **Dependency Injection**    | Manages type dependencies at runtime (e.g., constructor injection).                           | For dynamic systems with pluggable components. |
| **Schema Migration**        | Handles type evolution (e.g., adding/removing types without breaking existing code).           | During refactoring or backward-compatible changes. |
| **Graph Traversal**         | Explores type dependencies for analysis (e.g., dependency counting).                          | For static analysis tools.                      |
| **Constraint Solving**      | Resolves complex constraints (e.g., "X must implement Y or Z").                               | When relationships have multi-condition rules. |

---
**See Also**:
- [Dependency Inversion Principle (DIP)](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Open/Closed Principle (OCP)](https://en.wikipedia.org/wiki/Open%E2%80%93closed_principle) (for type extensibility).