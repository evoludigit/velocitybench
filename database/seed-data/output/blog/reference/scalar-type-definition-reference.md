# **[Pattern] Scalar Type Definition Reference Guide**

---
## **Overview**
The **Scalar Type Definition** pattern allows developers to extend GraphQL’s built-in scalar types (e.g., `String`, `Int`, `Boolean`) or introduce custom scalars (e.g., `Date`, `JSON`, `URL`) to handle domain-specific data types not natively supported. This pattern ensures type safety, improves query flexibility, and enables validation for complex or non-standard data formats.

Scalar types are specified in the **GraphQL schema** and implemented via custom serialization/deserialization logic (e.g., parsing input/output between JSON and native types). Common use cases include:
- Representing dates/times with timezone support.
- Validating nested JSON structures in queries.
- Handling binary data or UUIDs with custom formatting.

---

## **Schema Reference**
Scalar types are defined in the **type system** or **schema** using the following syntax:

| **Type**       | **Description**                                                                                     | **Example**                          |
|-----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **Built-in**    | Native GraphQL scalars (`Int`, `Float`, `String`, `Boolean`, `ID`).                                | `type: ID`                           |
| **Custom**      | User-defined scalars (e.g., `Date`, `JSON`, `LatLong`).                                            | `scalar Date`                        |
| **Coercing**    | Optional rules for parsing serialize/deserialize values (e.g., regex validation, format checks).   | `coerce(value: String): Date`         |

---

### **Custom Scalar Definition Syntax**
```graphql
# Minimal custom scalar definition
scalar Date

# Scalar with coercing rules
scalar Email @coerce(
  parse: "String!"  # Input type (query arguments)
  serialize: "String" # Output type (resolvers)
)
```

---

## **Key Implementation Concepts**
### **1. Scalar Registration**
Custom scalars must be registered in schema metadata (e.g., via `makeExecutableSchema` in Apollo Server or `importTypeDefinitions` in GraphQL.js):

```javascript
// Apollo Server example
const typeDefs = `
  scalar Date
`;

const resolvers = {
  Date: {
    // Custom logic for parsing/serializing
  },
};

// Register scalar via schema builder
const schema = makeExecutableSchema({ typeDefs, resolvers });
```

---

### **2. Coercion Logic**
Scalar types require **coercion functions** to validate and convert values between:
- **Query arguments** (input): `JSON.stringify` or manual parsing (e.g., `new Date(value)`).
- **Query responses** (output): Format data for clients (e.g., ISO-8601 strings).

#### **Example: `Date` Scalar**
```javascript
const resolvers = {
  Date: {
    parseValue(value) {  // Query argument parsing
      return new Date(value);
    },
    serialize(value) {   // Response formatting
      return value.toISOString();
    },
    parseLiteral(ast) {  // For GraphQL literals (e.g., `query { date: 2023-10-01 }`)
      return new Date(ast.value);
    },
  },
};
```

#### **Key Methods**:
| Method        | Purpose                                                                 |
|---------------|-------------------------------------------------------------------------|
| `parseValue`  | Handles input from client (e.g., `{"date": "2023-10-01"}`).             |
| `serialize`   | Formats output for client (e.g., `2023-10-01T00:00:00.000Z`).           |
| `parseLiteral`| Parses GraphQL literals (e.g., `query { node: 2023-10-01 }`).            |

---

### **3. Input Validation**
Scalar types can include **validation rules** (e.g., regex, format checks) in the schema:
```graphql
scalar Email @coerce(
  parse: "String!" @validate(regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
)
```

---

## **Query Examples**
### **1. Querying a Custom Scalar**
```graphql
query GetEvent {
  event(id: "123") {
    startTime: date  # Custom scalar field
    location: json   # Custom JSON scalar
  }
}
```

**Response:**
```json
{
  "data": {
    "event": {
      "startTime": "2023-10-01T12:00:00.000Z",
      "location": { "lat": 40.7, "lon": -74.0 }
    }
  }
}
```

---

### **2. Inputting Custom Scalars**
```graphql
mutation CreateUser {
  createUser(input: {
    birthDate: "1990-05-15"  # Parsed by Date scalar
    preferences: { theme: "dark" }  # JSON scalar
  }) {
    user { id }
  }
}
```

---

### **3. Built-in Scalar Usage**
```graphql
query GetUser {
  user(id: "123") {
    age: int  # Built-in scalar
    isActive: boolean
  }
}
```

---

## **Common Pitfalls & Solutions**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| **Unparsable dates/times**         | Use `Date` scalar with `parseValue`/`serialize` to enforce ISO-8601.         |
| **JSON parsing errors**             | Validate input JSON structure in `parseValue` or use `@validate` directives. |
| **Case sensitivity in IDs**        | Use `@coerce(parse: "String!")` to normalize case (e.g., lowercase).         |
| **Cross-platform timezone issues**  | Standardize on UTC in `serialize` and convert client-side.                   |

---

## **Advanced Patterns**
### **1. Nested Scalars**
Combine custom scalars with complex types:
```graphql
type GeoPoint {
  lat: Float!
  lon: Float!
}

scalar GeoPoint @coerce(
  parse: "String!" @validate(format: "LATITUDE_LONGITUDE")
)
```

---

### **2. Scalar Input Objects**
Use `@input` to group scalar fields (e.g., for mutations):
```graphql
input DateRange {
  start: Date!
  end: Date!
}

mutation FilterEvents {
  filterEvents(range: { start: "2023-10-01", end: "2023-10-31" }) {
    count
  }
}
```

---

### **3. Legacy System Integration**
Map custom scalars to third-party formats (e.g., database timestamps):
```javascript
const resolvers = {
  CreatedAt: {
    serialize(value) { // Convert to legacy format (e.g., "YYYY-MM-DD HH:MM:SS")
      return value.toLocaleString();
    },
  },
};
```

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **Use Case**                          |
|---------------------------|-----------------------------------------------------------------------------|----------------------------------------|
| **Input Object Types**    | Group input fields (e.g., for mutations).                                    | Filtering/searching with custom criteria. |
| **Directives**            | Add metadata (e.g., `@validate`) to scalars or fields.                      | Enforce regex, custom validation.      |
| **Interfaces/Unions**     | Abstract over multiple types sharing a scalar (e.g., `Node` with `ID`).     | Polymorphic queries.                  |
| **Subscription Scalars**  | Stream real-time data with custom scalar validation.                         | Live updates (e.g., WebSockets).      |
| **Persisted Queries**    | Cache scalar-heavy queries to reduce network overhead.                      | High-performance APIs.                |

---

## **Tools & Libraries**
| **Library**       | **Purpose**                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| Apollo Server     | Built-in scalar coercion support.                                           |
| GraphQL.js        | Custom scalar registration via `GraphQLScalarType`.                       |
| `graphql-scalars` | Opinionated scalar utilities (e.g., `date`, `json`).                       |
| `@graphql-tools`  | Schema stitching with custom scalars across microservices.                 |

---

## **Best Practices**
1. **Document Scalars Clearly**: Use `@description` in schema definitions.
2. **Leverage Coercion**: Always implement `parseValue`, `serialize`, and `parseLiteral`.
3. **Validate Early**: Use `@validate` directives to catch errors during parsing.
4. **Test Thoroughly**: Edge cases (e.g., malformed JSON, timezone offsets).
5. **Standardize Formats**: Enforce consistent serialization (e.g., ISO-8601 for dates).

---
**Example Full Schema with Scalars**:
```graphql
scalar Date
scalar JSON

type Event {
  id: ID!
  title: String!
  date: Date!
  metadata: JSON
}

input EventInput {
  title: String!
  date: Date!
  metadata: JSON
}

mutation CreateEvent($input: EventInput!) {
  createEvent(input: $input) {
    event { id }
  }
}
```