# **[Pattern] Thrift Protocol Patterns Reference Guide**

---

## **Overview**
The **Thrift Protocol Patterns** reference guide describes standardized ways to structure request/response interactions using Apache Thrift’s binary and compact protocols. Thrift is a high-performance RPC framework that supports multiple protocols (e.g., `TBinaryProtocol`, `TCompactProtocol`, `TJSONProtocol`), each with unique serialization and performance characteristics.

This guide covers:
- **Protocol selection** (synchronous vs. asynchronous, compactness vs. readability).
- **Message design patterns** (one-way, streaming, batching, validation).
- **Error handling and timeouts** (explicit failure modes, retry logic).
- **Serialization optimizations** (field types, nested structures, and schema evolution).

Properly applying these patterns ensures efficient data transfer, maintainability, and fault tolerance in distributed systems.

---

## **Schema Reference**
Below are common Thrift message schemas organized by pattern. Field types are standardized for consistency with Thrift’s type system.

| **Pattern**               | **Use Case**                          | **Schema Example**                                                                 | **Key Notes**                                                                                         |
|---------------------------|---------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **One-Way RPC**           | Fire-and-forget operations (e.g., logging). | `service OneWayService { void LogEvent(1: string message); }`                     | No response expected; use `TNonblockingTransport`.                                                   |
| **Request-Response**      | Synchronous interaction (e.g., queries).| `service UserService { 1: User GetUser(1: i32 userId) throws (4: UserNotFound); }` | Standard RPC; defines explicit error types.                                                          |
| **Streaming**             | Large payloads (e.g., file uploads).   | `service DataService { stream void UploadData(1: TStream<bytes> data); }`         | Handles chunked data with `TStream`; pair with streaming transport (`TStreamingTransport`).         |
| **Batched Requests**      | Bulk operations (e.g., batch inserts).| `service BatchService { 1: list<Result> BatchExecute(1: list<Operation> ops); }`   | Reduces round trips; use for idempotent operations.                                                   |
| **Validation**            | Schema-aware input/output checks.     | `service AuthService { 1: bool ValidateUser(1: User user) throws (1: InvalidUser); }` | Define custom error types (`InvalidUser`) for structured validation.                                 |
| **Pagination**            | Large datasets (e.g., search results).| `service SearchService { 1: list<User> Search(1: string query, 1: i32 limit, 1: i32 offset); }` | Use `offset/limit` or cursor-based pagination.                                                     |
| **Timeouts**              | Prevent hanging clients/servers.      | `service TimeoutService { 1: string CallWithTimeout(1: i32 durationMs) throws (1: TimeoutError); }` | Configure server-side timeouts via `TTransportFactory` factory settings.                          |

---

## **Query Examples**
### **1. One-Way RPC (Logging)**
**Client-side:**
```thrift
client = OneWayService.Client(SocketTransport("localhost", 9090), TBinaryProtocol())
client.LogEvent("User logged in at 2023-10-01T12:00:00Z")
```
- **Protocol:** `TBinaryProtocol` (default for efficiency).
- **Transport:** `TNonblockingTransport` ensures no blocking.

---

### **2. Request-Response (User Fetch)**
**Server-side (Thrift IDL):**
```thrift
service UserService {
  User GetUser(1: i32 userId)
    throws (1: string ErrorMessage),
           (2: i32 StatusCode);
}
```
**Client-side (Python):**
```python
user = client.GetUser(user_id=42)
if user.error:
    raise Exception(f"Error: {user.error}")
```
- **Error Handling:** Custom exceptions are returned as structured data.
- **Protocol:** `TCompactProtocol` can reduce payload size for large responses.

---

### **3. Streaming Upload**
**Client (Chunked Upload):**
```thrift
def upload_data(data_stream):
    client = DataService.Client(...)
    with TStreamingTransport(client.get_socket()) as transport:
        protocol = TCompactProtocol(transport)
        client.UploadData(protocol, data_stream)
```
- **Efficiency:** Streams data incrementally without full payload loading.
- **Transport:** `TStreamingTransport` handles chunked reads/writes.

---

### **4. Batched Operations**
**Server-side:**
```thrift
struct Operation {
  1: string type ("insert"|"delete"),
  2: User target_user
}
```
**Client-side (Bulk Insert):**
```python
ops = [
    {"type": "insert", "target_user": {"id": 1, "name": "Alice"}}
]
results = client.BatchExecute(ops)
```
- **Use Case:** Reduces latency by combining multiple calls into one.

---

### **5. Pagination (Offset-Based)**
**Server-side:**
```thrift
service SearchService {
  list<User> Search(1: string query,
                    1: i32 limit = 100,
                    1: i32 offset = 0);
}
```
**Client-side:**
```python
first_page = client.Search("users", limit=10, offset=0)
next_page = client.Search("users", limit=10, offset=10)
```
- **Optimization:** Avoid fetching all data at once.

---

## **Related Patterns**
1. **Thrift Service Design**
   - Standardize service interfaces (e.g., `TBase`, abstract service classes).
   - [Link to *Service Design Patterns* guide](#).

2. **Transport Selection**
   - Choose between blocking (`TSocket`) and non-blocking (`TNonblockingSocket`).
   - Optimize for latency (UDP) or reliability (TCP).

3. **Schema Evolution**
   - Use Thrift’s backward/forward compatibility rules for field additions/deletions.
   - Example: Mark optional fields as `optional` to allow schema changes.

4. **Security Patterns**
   - Encrypt transports (`TSSLTransportFactory`).
   - Validate inputs via `TValidator` interfaces.

5. **Performance Tuning**
   - **Protocol:** `TCompactProtocol` for small payloads; `TBinaryProtocol` for large.
   - **Serialization:** Prefer `i64` over `double` for timestamps to avoid precision loss.

---

## **Best Practices**
| **Practice**                     | **Guidance**                                                                 |
|-----------------------------------|------------------------------------------------------------------------------|
| **Protocol Selection**            | Use `TCompactProtocol` for JSON-like compactness; `TBinaryProtocol` for raw speed. |
| **Error Handling**                | Define custom error types in Thrift IDL (e.g., `InvalidInput`).              |
| **Timeouts**                      | Set `socket_timeout` in `TTransportFactory` (default: 30s).                  |
| **Streaming**                     | Use `TStreamingTransport` for large files (>1MB).                           |
| **Batching**                      | Limit batch size to 1000 operations to avoid memory overload.                |
| **Validation**                    | Enforce schema constraints at the server (e.g., `not_null` fields).        |

---
## **Common Pitfalls**
1. **Blocking Transports**
   - Avoid `TSocket` for high-latency operations; use `TNonblockingSocket` instead.

2. **Schema Incompatibility**
   - Field type changes (e.g., `string` → `binary`) break compatibility unless marked `optional`.

3. **Unbounded Streams**
   - Malicious clients may send infinite data; enforce size limits on streams.

4. **Ignoring Timeouts**
   - Server-side timeouts (`socket_timeout`) prevent hangs during network issues.

5. **Over-Batching**
   - Large batches increase memory usage and failure risk (e.g., network drops).

---
## **Further Reading**
- [Thrift Core Documentation](https://thrift.apache.org/docs/core/)
- [Protocol Comparisons](https://thrift.apache.org/docs/performance)
- [Service Development Guide](https://thrift.apache.org/docs/developing)