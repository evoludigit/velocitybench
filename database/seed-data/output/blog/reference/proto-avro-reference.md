# **[Pattern] Avro Protocol Patterns – Reference Guide**

---

## **Overview**
Avro Protocol Patterns define a structured, versioned schema language for serialized data exchange, enabling backward and forward compatibility across services. This pattern standardizes message formats, schema evolution, and serialization/deserialization using **Apache Avro**, ensuring efficient, language-agnostic communication with minimal overhead.

Key benefits include:
✔ **Schema evolution** – Seamless backward/forward compatibility.
✔ **Compact binary encoding** – Optimized for performance.
✔ **Rich metadata support** – Fields, nesting, and nested schemas.
✔ **Tooling-friendly** – Compatible with Avro, Protocol Buffers, and Thrift.

This guide covers implementation details, schema design best practices, and common pitfalls.

---

## **Schema Reference**
Avro schemas consist of **recursive types** with metadata support. Below are core schema definitions and their use cases.

| **Schema Type**       | **Definition**                                                                 | **Example**                                                                                     |
|-----------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Primitive Types**   | Fixed-length data (bool, int, string, bytes).                               | `"type": "int"`, `"type": "string"`                                                             |
| **Arrays**            | Lists of primitive or complex types.                                         | `"type": ["array", {"type": "string"}]`                                                       |
| **Maps**              | Key-value pairs (requires a primitive key type).                             | `"type": ["map", {"type": "string"}]`                                                          |
| **Records**           | Structured objects with named fields.                                        | `"type": "record", "name": "User", "fields": [{"name": "name", "type": "string"}]`             |
| **Enums**             | Fixed set of constants (e.g., status codes).                                | `"type": "enum", "name": "Status", "symbols": ["ACTIVE", "INACTIVE"]`                          |
| **Unions**            | Allows multiple schema types per field (e.g., nullable values).              | `"type": ["null", "int", "string"]`                                                          |
| **Fixed**             | Fixed-length binary data (e.g., UUIDs).                                      | `"type": "fixed", "size": 16, "name": "UUID"`                                                  |
| **Nested Records**    | Complex objects with nested schemas (e.g., arrays of records).               | `"type": "record", "name": "Order", "fields": [{"name": "items", "type": ["array", {"type": "record", "name": "Item", ...}]}]` |

---

## **Implementation Details**

### **1. Schema Design Principles**
- **Use records for structured data** (e.g., `User`, `Event`).
- **Prefer unions for nullable fields** (e.g., `["null", "string"]`).
- **Avoid deep nesting** (limit to <3 levels) for performance.
- **Document default values** in comments for backward compatibility.

### **2. Schema Evolution**
Avro supports **three evolution modes** for backward/forward compatibility:

| **Mode**               | **Allowed Changes**                                      | **Example**                                                                                     |
|------------------------|---------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Breaking**           | New fields, renamed fields, changed types.             | Add `"age": {"type": "int"}` (new field).                                                    |
| **Non-breaking**       | New optional fields (default `null`).                   | Add `"age": ["null", "int"]` (default `null`).                                               |
| **Dynamic** (Advanced) | Fields can be added/removed at runtime via schemas.    | Requires custom deserialization logic.                                                       |

**Best Practice**: Default to **non-breaking** unless you need strict versioning.

### **3. Serialization/Deserialization**
- **Binary Format**: Compact and efficient (default for Avro).
  ```java
  // Java Example (Avro Library)
  DatumWriter<User> writer = new SpecificDatumWriter<>(User.class);
  BinaryEncoder encoder = EncoderFactory.get().binaryEncoder(outputStream, null);
  writer.write(user, encoder);
  encoder.flush();
  ```
- **JSON Format**: Human-readable (for debugging).
  ```bash
  avro-tools to-json --schema schema.avsc data.avro > data.json
  ```

### **4. Versioning & Compatibility**
- **Schema IDs**: Assign unique IDs to schemas (e.g., `1.0`, `2.0`).
- **Schema Registry**: Store schemas in a service like **Confluent Schema Registry** or **Apache Avro’s `avro-tools`**.
- **Compatibility Checks**:
  ```bash
  avro-tools validate --schema1 schema-v1.avsc --schema2 schema-v2.avsc
  ```

---

## **Query Examples**
### **1. Writing Data (Java)**
```java
// Define schema (inline or external)
Schema schema = new Schema.Parser().parse("{\"type\":\"record\",\"name\":\"User\",\"fields\":[{\"name\":\"name\",\"type\":\"string\"}]}");

// Create data
Map<String, Object> user = new HashMap<>();
user.put("name", "Alice");

// Serialize
DatumWriter<User> writer = new SpecificDatumWriter<>(User.class);
DatumReader<User> reader = new SpecificDatumReader<>(User.class, schema);
ByteBuffer buffer = ByteBuffer.allocate(1024);
BinaryEncoder encoder = EncoderFactory.get().binaryEncoder(buffer, null);
writer.write(user, encoder);
encoder.flush();
byte[] bytes = buffer.array();
```

### **2. Reading Data (Python)**
```python
from avro.io import DatumReader, DatumWriter
from avro.datafile import DataFileReader, DataFileWriter
import io

# Define schema
schema = {
    "type": "record",
    "name": "User",
    "fields": [{"name": "name", "type": "string"}]
}

# Write data
writer = DataFileWriter(open("output.avro", "wb"), DatumWriter(schema))
writer.append({"name": "Bob"})
writer.close()

# Read data
reader = DataFileReader(open("output.avro", "rb"), DatumReader(schema))
for record in reader:
    print(record["name"])  # Output: Bob
reader.close()
```

### **3. Schema Evolution Example (Add Field)**
**Before (v1.avsc)**:
```json
{"type": "record", "name": "User", "fields": [{"name": "name", "type": "string"}]}
```

**After (v2.avsc, non-breaking)**:
```json
{"type": "record", "name": "User", "fields": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": ["null", "int"]}
]}
```

**Java Code (Handles Evolution)**:
```java
// v1 data can still read v2 schema (age defaults to null)
DatumReader<User> reader = new SpecificDatumReader<>(User.class, schema_v2);
User user = reader.read(null, buffer);
System.out.println(user.getAge());  // Output: null (if not set in v1)
```

---

## **Common Pitfalls & Solutions**

| **Pitfall**                          | **Solution**                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------|
| **Schema drift** (unintended changes) | Use a **schema registry** to enforce versioning.                          |
| **Performance bottlenecks** (deep nesting) | Limit nesting depth; use **arrays/maps** for large datasets.             |
| **Null handling** (missing fields)   | Explicitly declare unions (`["null", "type"]`).                            |
| **Cross-language compatibility**     | Test schemas across languages (e.g., Java/Python).                          |
| **Large schemas** (serialization overhead) | Split into modular schemas (e.g., `User`, `Address`).                     |

---

## **Related Patterns**
1. **[Schema Registry Pattern]** – Centralized schema management (e.g., Confluent, Apache Griffin).
2. **[Event-Driven Architecture with Avro]** – Schema-based event serialization (e.g., Kafka Avro Serializer).
3. **[IDL-to-Avro Conversion]** – Generate Avro schemas from **Protocol Buffers** or **Thrift**.
4. **[Data Contract Testing]** – Validate schemas using tools like **SchemaSpy** or **Great Expectations**.

---
**Further Reading**:
- [Apache Avro Docs](https://avro.apache.org/docs/current/)
- [Avro Protocol Buffers Alternative](https://avro.apache.org/docs/current/idl/)
- [Kafka Avro Serializer](https://kafka.apache.org/documentation/#avro_serializer)

---
**Last Updated**: [MM/YYYY]
**Version**: 1.2