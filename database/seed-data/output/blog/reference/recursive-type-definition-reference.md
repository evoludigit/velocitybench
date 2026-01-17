# **[Pattern] Recursive Type Definition Reference Guide**

---

## **Overview**
A **Recursive Type Definition** pattern enables defining a data structure that references itself, forming nested or hierarchical relationships. This pattern is crucial for modeling complex objects such as:
- **Tree structures** (e.g., file systems, organizational hierarchies)
- **Graphs** (e.g., social networks, dependency trees)
- **Linked lists** or self-contained nodes (e.g., JSON-LD, YAML anchors)

In languages/APIs supporting open-world or self-referential types, this pattern avoids infinite definitions by using **type aliases, references, or graph traversal rules**. Common use cases include:
- **Nested configurations** (e.g., nested JSON schemas)
- **Documentation metadata** (e.g., Markdown links to other pages)
- **Dependency resolution** (e.g., build systems where tasks reference other tasks).

---

## **Schema Reference**
Below are key constructs for implementing recursive types across APIs, JSON schemas, and programming languages. Adjust field names to fit your use case.

| **Component**               | **Description**                                                                                     | **Example**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Base Type (Self-Reference)** | The primary type that holds recursive data.                                                           | `{ id: string, children?: RecursiveNode[] }`                                                     |
| **Recursive Alias**         | A placeholder for the same type (avoids circular references in strict languages like TypeScript).    | `type RecursiveNode = { ... } & { children?: RecursiveNode[] };`                                |
| **Distinct Node Types**     | Subtypes with unique properties for hierarchical differentiation (e.g., `NodeType: "file" | "folder"`). | `{ type: string, name: string, children?: Node[] }`                                            |
| **Graph Traversal Rules**   | Metadata or logic to control recursion depth (e.g., `maxDepth`, `recursive: boolean`).            | `{ maxDepth?: number, recursive: false/true }`                                                  |
| **Reference Fields**        | Explicit pointers to other nodes (e.g., `parentId` or `ref` links).                                | `{ parentId: string, children: [{ ref: "#node123" }] }`                                          |
| **External Schema Link**    | JSON Schema’s `$ref` or OpenAPI’s `$schema` to resolve nested types dynamically.                   | `$ref: "#/components/schemas/RecursiveNode"`                                                     |

---

## **Implementation Examples**

### **1. JSON Schema (Self-Referential)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "name": { "type": "string" },
    "children": {
      "type": "array",
      "items": "$ref": "#"
    }
  },
  "required": ["id", "name"]
}
```

**Key Notes**:
- `$ref` creates a self-loop (supported in tools like `json-schema-validator`).
- For **strict parsers**, use `$dynamicRef` or a pre-processing step to resolve references.

---

### **2. TypeScript (Type Aliases)**
```typescript
type Node = {
  id: string;
  name: string;
  children?: Node[]; // Self-reference
};

const tree: Node = {
  id: "1",
  name: "Root",
  children: [
    { id: "2", name: "Child Node" } // No infinite loop at compile time
  ]
};
```

**Key Notes**:
- TypeScript **infers** recursive types but does *not* validate runtime circularity.
- For complex graphs, use **graph libraries** (e.g., `ts-graphviz`).

---

### **3. YAML (Anchors)**
```yaml
node:
  id: root
  name: Parent
  children:
    - !ref node-01
node-01:
  id: child
  name: Leaf
  children: []  # YAML anchors avoid duplication
```

**Key Notes**:
- Anchors (`!ref`) link to previous nodes (requires YAML processor support).
- Works in CI/CD tools (e.g., GitLab CI variables).

---

### **4. REST API (GraphQL-like Response)**
```json
{
  "resolvedNode": {
    "id": "123",
    "name": "Project",
    "children": [
      { "id": "456", "name": "Module", "children": [] }
    ]
  },
  "maxDepth": 2  // Prevents infinite loops
}
```

**Key Notes**:
- **Server-side**: Implement depth-limiting queries (e.g., `SELECT * FROM nodes WHERE depth < maxDepth`).
- **Client-side**: Use `Fetch` with `AbortController` for depth-controlled requests.

---

## **Query Examples**
### **SQL (Recursive CTE)**
```sql
WITH RECURSIVE TreeCTE AS (
  SELECT id, name, parent_id = NULL AS depth
  FROM nodes WHERE id = 'root'
  UNION ALL
  SELECT n.id, n.name, c.depth + 1
  FROM nodes n
  JOIN TreeCTE c ON n.parent_id = c.id
)
SELECT * FROM TreeCTE;
```

**Key Notes**:
- Replace `UNION ALL` with `UNION` to deduplicate (slower but correct).
- Add `WITH (MAXRECURSION n)` in SQL Server to prevent stack overflow.

---

### **Python (Graph Traversal)**
```python
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class Node:
    id: str
    name: str
    children: Optional[list['Node']] = None

def traverse(node: Node, depth: int = 0) -> None:
    if depth > 2:  # Safety limit
        return
    print(f"{'  ' * depth}- {node.name}")
    if node.children:
        for child in node.children:
            traverse(child, depth + 1)
```

**Key Notes**:
- **Cyclic graphs**: Use `sys.setrecursionlimit` or iterative DFS (e.g., with a stack).
- Libraries: `networkx` for complex graphs.

---

## **Error Handling & Edge Cases**
| **Scenario**               | **Solution**                                                                                     |
|----------------------------|--------------------------------------------------------------------------------------------------|
| Infinite recursion         | Set `maxDepth` or use iterative traversal (e.g., BFS/DFS with a visited set).                |
| Circular references        | Validate with `JSON.parse(JSON.stringify(data), reviver)` (for JSON).                           |
| Schema validation failures | Use `ajv` (JSON Schema validator) with `{ allErrors: true }` to catch invalid recursive fields. |
| Large graphs                | Stream data (e.g., `readline` in Python) or paginate API responses with `?limit=100`.           |

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                  | **When to Use**                                                                                  |
|----------------------------------|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **[Composite Pattern]**          | Encapsulates recursive structures as single objects (e.g., `File` and `Folder` both extend `Node`). | When you need polymorphic tree nodes (e.g., GUI components).                                      |
| **[Graph Database Model]**       | Stores relationships as edges (e.g., Neo4j).                                                      | For highly interconnected data (e.g., recommendation engines).                                    |
| **[Lazy Loading]**               | Loads recursive data on-demand (e.g., `loadChildren()` in Vue.js).                                | Optimize performance for deep hierarchies.                                                      |
| **[Flattened JSON]**             | Converts nested structures to arrays (e.g., `children: [{ id: "1", depth: 1 }]`).                 | Simplify querying (e.g., in time-series databases like InfluxDB).                                |
| **[Visitor Design Pattern]**     | Defines operations for recursive traversal (e.g., `accept(Visitor)`).                            | When you need to process nodes differently (e.g., validation, serialization).                     |

---

## **Best Practices**
1. **Depth Limitation**: Always cap recursion to avoid stack overflows.
   ```python
   max_depth = 10
   current_depth = 0
   if current_depth >= max_depth: raise RecursionError
   ```

2. **Idempotency**: Use immutable IDs (e.g., UUIDs) to avoid reference loops during updates.
   ```json
   { "ref": "#/components/schemas/Node/12345" }  // Stable reference
   ```

3. **Tooling**:
   - **Validation**: `json-schema-validator` for JSON schemas.
   - **Visualization**: `mermaid.js` for rendering recursive structures in docs.
   - **Testing**: Mock recursive data with `factory-boy` (Python) or `jest.mock()`.

4. **Performance**:
   - Cache resolved nodes (e.g., Redis for API responses).
   - Use **denormalized** fields for performance-critical queries (e.g., `parent_id`).

---
**Further Reading**:
- [JSON Schema Recursion](https://json-schema.org/understanding-json-schema/reference/recursive.html)
- [TypeScript Handbook: Recursion](https://www.typescriptlang.org/docs/handbook/advanced-types.html#recursive-types)
- [GraphQL Depth Limiting](https://graphql.org/learn/global-objects/)