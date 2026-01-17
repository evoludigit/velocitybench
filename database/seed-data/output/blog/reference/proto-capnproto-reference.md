---
# **[Pattern] CAP'n Proto (capnp) Protocol Patterns Reference Guide**

---

## **Overview**
This reference guide documents **CAP'n Proto (capnp)** protocol patterns, a high-performance, language-neutral binary data format and serialization library. capnp excels in **inter-process communication (IPC), network protocols, configuration storage, and compiler-generated interfaces**, offering **type safety, schema evolution, and binary efficiency**.

Key features:
- **Schema-first design**, enabling compile-time safety and tooling (e.g., `capnpc` schema compiler).
- **Binary encoding** with **no runtime overhead** (unlike JSON/XML).
- **Evolvable schemas** (backward and forward compatibility).
- **Multi-language support** (C++, Java, Go, Rust, etc.).
- **Strong typing** to prevent runtime errors (e.g., mismatched field types).

This guide covers **common implementation patterns**, **schema design best practices**, **query examples**, and **anti-patterns** to ensure optimal performance and maintainability.

---

## **Schema Reference**
Below are fundamental **capnp schema constructs** and their use cases.

| **Schema Element**       | **Purpose**                                                                                     | **Example**                                                                 | **Notes**                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Struct**               | Defines a custom data type with named fields.                                                  | `struct User { name: Text; age: UInt16; }`                                 | Equivalent to a class/object in OOP.                                                           |
| **Union**                | A type that can hold one of several alternatives.                                               | `union Result { ok: Int32; error: Text; }`                                  | Useful for return values/errors.                                                             |
| **List**                 | A dynamically sized array of a specific type.                                                 | `list<User> employees;`                                                     | Fixed-size arrays use `Vector<n>`.                                                           |
| **Text/Bytes**           | Variable-length UTF-8 strings or binary data.                                                  | `text: Text; binaryData: Bytes;`                                            | `Text` is zero-indexed, `Bytes` allows raw binary.                                           |
| **Enum**                 | Named integer constants for type-safe options.                                                | `enum Status { Active = 1; Inactive = 2; }`                                 | Encodes as a single byte (small enums).                                                     |
| **Repeat**               | Indicates a group of fields that can be repeated (like `@repeat` in JSON Schema).              | `@repeat Message; @end`                                                     | Used in schema fragments for extensibility.                                                  |
| **Handler Interface**    | Defines RPC-like method signatures for remote procedures.                                     | `interface UserService { getUser(id: UInt32): User; }`                      | Compiles to language-specific RPC stubs.                                                     |
| **Error**                | Custom error types with payloads for diagnostic info.                                          | `error InvalidInput { code: UInt16; message: Text; }`                      | Extends capnp’s built-in error system.                                                         |
| **@cstruct**             | Maps to C structs (useful for interop with C libraries).                                     | `@cstruct { int32_t id; uint8_t flags; }`                                  | Avoids serialization overhead for performance-critical data.                                 |

---

## **Implementation Patterns**

### **1. Schema Design Best Practices**
- **Use `@exists` for Optional Fields**
  - Mark fields as nullable to avoid runtime errors when values are missing.
  - ```capnp
    field presence: @exists;
    field value: Int32 @exists(presence);
    ```
- **Prefer `Text` Over `String`**
  - `Text` is more efficient for variable-length strings (no null terminator).
- **Leverage `@const` for Constants**
  - Define immutable values in schemas:
    ```capnp
    @const PI = 3.14159;
    ```
- **Group Related Fields with `@repeat`**
  - Use schema fragments for extensible data (e.g., plugins):
    ```capnp
    @repeat PluginConfig;
    @end
    field name: Text;
    field version: UInt32;
    ```

### **2. Serialization & Deserialization**
- **Compile Schemas with `capnpc`**
  Generated code includes:
  - **Reader/Writer interfaces** (e.g., `UserReader`, `UserBuilder`).
  - **Type-safe accessors** (e.g., `user.getName()`).
  - **Memory management** (ownership semantics via `capnp::MallocMessage`).
  ```bash
  capnpc --lang=c++ user.capnp  # Generates C++ bindings
  ```
- **Binary Encoding Efficiency**
  - capnp uses **delta encoding** for integers and **length-prefixed fields**.
  - Example (serialized `User`):
    ```
    0x01 (name exists) + 3 (length: "Alice") + "Alice" + 0x04 0x19 (age: 25)
    ```

### **3. Remote Procedure Calls (RPC)**
- **Generate RPC Handlers**
  Define interfaces in `.capnp`:
  ```capnp
  interface Calculator {
    add(a: Int32, b: Int32): Int32;
  }
  ```
  Compile to client/server stubs:
  ```cpp
  auto calc = CalculatorClient(new Connection("tcp://localhost"));
  int result = calc->add(1, 2);  // Blocking call
  ```
- **Asynchronous RPC with `capnp::Async`**
  Use coroutines or async frameworks (e.g., C++17 `std::async`):
  ```cpp
  auto future = calc->addAsync(1, 2);
  future.then([](int res) { std::cout << res; });
  ```

### **4. Schema Evolution**
- **Backward Compatibility**
  - Add new fields or enums (existing code ignores unknown fields).
  - Remove fields **only if unused** (use `@deprecated` for warnings):
    ```capnp
    field oldField: Int32 @deprecated("Use newField instead");
    ```
- **Forward Compatibility**
  - Include `@repeat` for extensible schemas.
  - Use `@const` for stable values.

### **5. Performance Optimizations**
- **Reuse Messages**
  Avoid allocating new `Message` objects repeatedly:
  ```cpp
  capnp::MallocMessageBuilder message(1024);
  auto user = message.initRoot<User>();
  ```
- **Minimize Serialization Overhead**
  - Flatten nested structs to reduce binary size.
  - Use `UInt8` for enums (smaller than `Int32`).
- **Zero-Copy Reading**
  Use `Reader` objects to avoid copying data:
  ```cpp
  std::vector<uint8_t> buffer;
  capnp::ReaderOptions options;
  auto reader = capnp::Reader(buffer.data(), buffer.size(), options);
  ```

---

## **Query Examples**
### **1. Basic Struct Serialization (C++)**
```cpp
#include <capnp/message.h>
#include <capnp/cpp/message_builder.h>

int main() {
  capnp::MallocMessageBuilder message;
  auto user = message.initRoot<User>();
  user->setName("Alice");
  user->setAge(25);

  std::vector<uint8_t> data;
  message.getPointer()->serialize(data);  // Serialize to binary
  // ... transmit data ...
}
```

### **2. Deserializing and Querying (Go)**
```go
package main

import (
	"bytes"
	"github.com/apple/capnproto/go/capnp"
)

func main() {
	data := []byte{...}  // Binary data from capnp
	reader, _ := capnp.NewReader(bytes.NewReader(data))
	user := reader.RootAsUser().AsStruct()

	name := user.Name().AsText().String()
	age := user.Age()
}
```

### **3. RPC Server (C++)**
```cpp
#include <capnp/server.h>
#include <capnp/fault.h>

class CalculatorServer : public CalculatorServerBase {
  int32_t add(int32_t a, int32_t b) override {
    return a + b;
  }
};

int main() {
  capnp::Server server;
  server.AddService<CalculatorServer>(calc);
  server.Listen("tcp://:8080");
  server.Serve();
}
```

### **4. Schema Fragment for Extensibility**
```capnp
@repeat PluginConfig;
@end

struct PluginConfig {
  name: Text;
  version: UInt32;
  @exists hasSettings;
  settings: Settings @exists(hasSettings);
}

struct Settings {
  @repeat ConfigOption;
  @end
  key: Text;
  value: Text;
}
```

---

## **Common Pitfalls & Anti-Patterns**
| **Pitfall**                          | **Solution**                                                                 |
|---------------------------------------|------------------------------------------------------------------------------|
| **Ignoring `@exists` for optional fields** | Always check field existence to avoid crashes.                              |
| **Overusing nested structs**           | Flatten data to reduce binary overhead.                                     |
| **Not handling schema evolution**     | Test backward/forward compatibility early.                                  |
| **Blocking RPC calls in high-latency apps** | Use async RPC or timeouts.                                                |
| **Leaking memory with `MallocMessage`** | Use `MessageBuilder` for in-memory operations and `MallocMessage` for I/O. |
| **Mixing capnp with JSON for APIs**    | capnp is binary-only; use JSON for HTTP APIs separately.                     |

---

## **Related Patterns**
1. **[Schema-First APIs](https://example.com/schema-first)**
   - Design APIs around schemas (e.g., GraphQL-like queries but with capnp).
2. **[Binary Protocol Interop](https://example.com/binary-interop)**
   - Integrate capnp with Protocol Buffers or MessagePack via schema adapters.
3. **[Efficient Serialization](https://example.com/efficient-serialization)**
   - Compare capnp’s binary size vs. Protocol Buffers/MessagePack.
4. **[RPC with gRPC](https://example.com/rpc-grpc-capnp)**
   - Use capnp for data serialization with gRPC’s transport layer.
5. **[Type-Safe Configuration](https://example.com/type-safe-config)**
   - Store configs in capnp files (e.g., `config.capnp`) for validation.

---
**See Also:**
- [capnproto GitHub](https://github.com/apple/capnproto)
- [Schema Compiler (`capnpc`) Docs](https://capnproto.org/lang.html)
- [Language-Specific Guides](https://capnproto.org/lang-cpp.html)