# **[Pattern] Edge Conventions – Reference Guide**

---

## **Overview**
The **Edge Conventions** pattern defines a structured approach for modeling and querying relationships at the edges of a graph, ensuring consistency and predictability in how nodes interact across different domains (e.g., user interactions, event triggers, or dependency flows). It standardizes how **edges** (connections between nodes) are labeled, validated, and traversed, reducing ambiguity and improving maintainability in graph-based systems.

This pattern is particularly useful in:
- **Graph databases** (e.g., Neo4j, Amazon Neptune, ArangoDB)
- **Event-driven architectures** (e.g., Kafka, AWS EventBridge)
- **API workflows** (e.g., microservices composition, workflow orchestration)
- **Social/network graph applications** (e.g., recommendation engines, activity tracking)

By enforcing conventions for edge properties (e.g., `timestamp`, `weight`, `metadata`), applications can leverage standard traversal patterns (e.g., `OUTGOING`, `INCOMING`, `BIDIRECTIONAL`) without hardcoding logic.

---

## **Key Concepts**
1. **Edge Types**: Predefined labels (e.g., `follows`, `purchases`, `triggers`) that categorize relationships.
2. **Directionality**:
   - `OUTGOING`: From source node → target node (e.g., `USER → POST`).
   - `INCOMING`: Into the target node (e.g., `POST ← COMMENT`).
   - `BIDIRECTIONAL`: Symmetric edges (e.g., `FRIENDSHIP`).
3. **Edge Properties**: Standardized attributes (e.g., `createdAt`, `priority`, `customMetadata`).
4. **Traversal Rules**: How edges are navigated (e.g., `MATCH (a)-[e:TRIGGERS]->(b)`).

---

## **Schema Reference**
Below is the **standard schema** for edges in this pattern. Customize properties as needed.

| **Property**          | **Type**       | **Description**                                                                 | **Required?** | **Example Values**                          |
|-----------------------|----------------|---------------------------------------------------------------------------------|---------------|---------------------------------------------|
| `edgeType`            | String         | Predefined label (e.g., `follows`, `purchases`).                                 | Yes           | `"likes"`, `"subscribes_to"`                |
| `direction`           | Enum           | `OUTGOING`, `INCOMING`, or `BIDIRECTIONAL`.                                     | Yes           | `"OUTGOING"`                                 |
| `timestamp`           | ISO 8601 Date  | When the edge was created.                                                       | Yes           | `"2023-01-15T12:00:00Z"`                   |
| `weight`              | Float          |Numeric priority (e.g., for ranking).                                            | No            | `3.7` (e.g., trust score)                  |
| `metadata`            | JSON           | Custom key-value pairs (e.g., `{"campaign_id": "xyz123"}`).                       | No            | `{"status": "active"}`                     |
| `sourceNodeId`        | ID (String/Int) | ID of the originating node.                                                     | Yes*          | `"user_42"` (derived from traversal)       |
| `targetNodeId`        | ID (String/Int) | ID of the destination node.                                                     | Yes*          | `"product_123"`                              |
| `isVerified`          | Boolean        | Indicates if the edge has been validated (e.g., by an admin).                   | No            | `true`/`false`                               |
| `ttl`                 | Seconds (Int)  | Time-to-live for auto-cleanup (e.g., temporary edges).                          | No            | `86400` (24 hours)                         |

*Automatically populated during edge creation based on traversal context.

---

## **Implementation Details**
### **1. Edge Creation**
Edges must adhere to the schema. Example payloads:

#### **Cypher (Neo4j)**
```cypher
// Create a BIDIRECTIONAL "FRIENDSHIP" edge
MATCH (u:User {id: "user_1"}), (v:User {id: "user_2"})
CREATE (u)-[e:FRIENDSHIP {
  direction: "BIDIRECTIONAL",
  timestamp: datetime(),
  metadata: {since: "2023-01-01"}
}]->(v);
```

#### **REST API (Standard Request)**
```json
{
  "sourceNodeId": "user_1",
  "targetNodeId": "product_123",
  "edgeType": "purchases",
  "direction": "OUTGOING",
  "timestamp": "2023-01-15T12:00:00Z",
  "weight": 1.0,
  "metadata": {
    "payment_method": "credit_card",
    "discount_applied": true
  }
}
```

### **2. Edge Validation**
- **Directionality**: Reject edges where `direction` conflicts with traversal (e.g., `INCOMING` edge from `A->B`).
- **Timestamp**: Default to `NOW()` if not provided.
- **Metadata**: Validate against a JSON schema (e.g., using OpenAPI or JSON Schema).

### **3. Traversal Rules**
Use standard patterns for querying edges:
| **Use Case**               | **Cypher Query**                                                                 | **Gremlin (TinkerPop)**                          |
|----------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| Find all outgoing edges     | `MATCH (a)-[e]->(b) WHERE e.edgeType = "follows"`                                | `g.V().outE().has("edgeType", "follows")`       |
| Filter by weight           | `MATCH ()-[e:TRIGGERS]->() WHERE e.weight > 2.0`                                 | `g.E().has("weight", P.gt(2.0))`                 |
| Bidirectional lookup       | `MATCH (a)-[e:FRIENDSHIP]-(b)`                                                  | `g.V("user_1").bothE("FRIENDSHIP")`              |
| Add metadata dynamically   | `MATCH ()-[e]->() SET e.metadata.status = "active"`                            | `g.E().property("metadata", "status", "active")` |

---

## **Query Examples**
### **Example 1: Get Top 5 High-Weight Edges**
**Goal**: Retrieve the 5 most "important" edges (e.g., `weight > 5.0`) from a node.
**Cypher**:
```cypher
MATCH (user:User {id: "user_42"})-[e]->()
WHERE e.weight > 5.0
RETURN e, e.targetNodeId AS productId, e.weight
ORDER BY e.weight DESC
LIMIT 5;
```
**Output**:
| `edge`               | `productId` | `weight` |
|----------------------|-------------|----------|
| `[purchases]`        | `product_5` | 9.2      |
| `[recommends]`       | `product_3` | 7.8      |

---

### **Example 2: Event-Driven Filtering**
**Goal**: Find all `subscribes_to` edges where `metadata.channel = "newsletter"`.
**Cypher**:
```cypher
MATCH (user:User)-[e:subscribes_to]->()
WHERE e.metadata.channel = "newsletter"
RETURN user.id, e.targetNodeId AS newsletterId;
```
**Output**:
| `user.id` | `newsletterId` |
|-----------|----------------|
| `user_10` | `newsletter_A` |

---

### **Example 3: TTL-Based Cleanup**
**Goal**: Delete edges older than 30 days (TTL = `86400` seconds × 30).
**Cypher**:
```cypher
MATCH ()-[e]->() WHERE datetime() - e.timestamp > duration('P30D')
DELETE e;
```

---

## **Best Practices**
1. **Standardize Edge Types**:
   - Use lowercase with underscores (e.g., `user_creates_post` instead of `userCreatesPost`).
   - Document edge types in a central registry.

2. **Optimize for Traversal**:
   - Index edge properties frequently used in queries (e.g., `edgeType`, `timestamp`).
   - Precompute aggregations (e.g., `COUNT(e)` for node degrees).

3. **Handle Bidirectional Edges**:
   - Use `MERGE` to avoid duplicates:
     ```cypher
     MATCH (a), (b)
     MERGE (a)-[e:FRIENDSHIP]->(b)
     ON CREATE SET e.timestamp = datetime()
     ON MATCH SET e.timestamp = datetime();
     ```

4. **Versioning**:
   - Append a suffix to edge types during major schema changes (e.g., `purchases_v2`).

5. **Security**:
   - Restrict edge creation/deletion via ACLs (e.g., only `ADMIN` can set `isVerified = true`).

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                                  |
|---------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **[Node Conventions]**     | Standardizes node schemas (e.g., `User`, `Product`).                       | Pair with Edge Conventions for complete schema.  |
| **[Traversal Patterns]**   | Optimizes graph traversals (e.g., depth-first, shortest path).             | Use when querying complex relationships.        |
| **[Event Sourcing]**      | Stores state changes as immutable edges.                                   | For audit trails or replayable workflows.        |
| **[Schema Evolution]**    | Manages backward-compatible schema changes.                               | When adding optional edge properties.           |
| **[Graph Partitioning]**  | Distributes edges across partitions for scalability.                       | In large-scale graph databases.                  |

---

## **Edge Cases & Mitigations**
| **Edge Case**                     | **Solution**                                                                 |
|------------------------------------|------------------------------------------------------------------------------|
| Duplicate edges (e.g., bidirectional `FRIENDSHIP`) | Use `MERGE` or unique constraints on `(source, edgeType, target)`.         |
| Missing `timestamp`                | Auto-populate with `datetime()` during creation.                           |
| Malformed `metadata`               | Validate against a JSON schema (e.g., using a tool like [JSON Schema Validator](https://www.jsonschemavalidator.net/)). |
| Directional conflicts             | Reject edges where `direction` contradicts traversal (e.g., `INCOMING` edge from `A->B`). |
| High-cardinality edges             | Shard edges by `edgeType` or use edge labels for indexing.                |

---
**Final Notes**:
- Extend this pattern for domain-specific needs (e.g., add `confidenceScore` for recommendation edges).
- Document edge types in a **graph schema registry** (e.g., AWS Glue Schema Registry, Collibra).
- Monitor edge creation/deletion rates for anomalies (e.g., sudden spikes may indicate abuse).