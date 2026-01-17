# **Debugging "gRPC Anti-Patterns": A Troubleshooting Guide**

gRPC is a powerful RPC (Remote Procedure Call) framework, but improper usage can lead to performance bottlenecks, scalability issues, and system instability. This guide covers **common gRPC anti-patterns**, their symptoms, debugging techniques, and preventive strategies to ensure efficient and maintainable gRPC-based systems.

---

## **1. Symptom Checklist**

Before diving into fixes, identify these warning signs:

| **Symptom**                          | **Possible Cause**                          | **Impact**                          |
|--------------------------------------|--------------------------------------------|-------------------------------------|
| High **latency** in gRPC calls       | Unoptimized payloads, slow serialization, network bottlenecks | Poor user experience |
| **High memory consumption**          | Streaming issues, unbounded buffers, leakers | System crashes, OOM errors |
| **Connection leaks** (dropped clients) | Unclosed streams, missing contextManagement | Resource exhaustion |
| **Thundering Herd Problem**          | Lack of connection pooling or load balancing | Server overload |
| **Deadlocks or hangs**               | Blocking calls in async contexts, improper mutation | Unresponsive API |
| **Error: "Connection refused"**      | Misconfigured load balancing, DNS issues, firewall blocks | API failures |
| **Uneven load distribution**         | Poor client-side retries, missing circuit breakers | Hotspots in backend |
| **Premature stream closure**         | Incorrect `grpc-go` stream handling | Data loss |
| **Excessive TLS handshakes**         | No connection reuse, poor TLS tuning | Network overhead |

If any of these occur, proceed to diagnostics.

---

## **2. Common gRPC Anti-Patterns & Fixes**

### **1. Anti-Pattern: Unoptimized Payloads**
**Problem:** Sending large binary data (e.g., images, PDFs) over gRPC without compression or chunking.

**Symptoms:**
- Slow RPC responses
- High bandwidth usage
- Timeout errors

**Fix:**
Use **gzip compression** and **streaming** for large responses.
```go
// Enable compression in client-side transport
clientConn, err := grpc.Dial(
    "example.com:50051",
    grpc.WithTransportCredentials(insecure.NewCredentials()),
    grpc.WithCompressor("gzip"), // Enable compression
)
if err != nil { ... }

// In server, ensure compression is supported
grpc_server := grpc.NewServer(
    grpc.Compressor(registry.DefaultCompressor),
)
```

**Alternative:** Use **chunked streaming** (for very large files):
```go
stream, err := client.GetLargeData(ctx)
if err != nil { ... }
for {
    chunk, err := stream.Recv()
    if err == io.EOF { break }
    if err != nil { ... }
    process(chunk.Data) // Process in chunks
}
```

---

### **2. Anti-Pattern: Not Closing Streams Properly**
**Problem:** Unclosed gRPC streams cause **connection leaks** and **memory bloat**.

**Symptoms:**
- `error: "connection reset by peer"`
- Increasing connection count over time
- Server-side memory exhaustion

**Fix:** Always **close streams** explicitly.
```go
// Client-side stream
respStream, err := client.StreamData(ctx)
if err != nil { ... }
defer respStream.CloseSend() // Ensure stream is closed

// Server-side stream
for {
    req, err := stream.Recv()
    if err == io.EOF {
        return nil, status.Error(codes.Cancelled, "stream closed")
    }
    // Process...
}
stream.SendAndClose(&response) // Close after sending
```

**Use `context` for cancellation:**
```go
// Gracefully close with context
go func() {
    <-ctx.Done()
    stream.SendAndClose(&response)
}()
```

---

### **3. Anti-Pattern: Blocking Calls in Async Contexts**
**Problem:** Using **synchronous RPC calls** in Goroutines, leading to **deadlocks**.

**Symptoms:**
- Hangs with `goroutine 1 leaked`
- `panic: runtime error: goroutine stack exceeds 1000000000-byte limit`
- Deadlocks in high-concurrency scenarios

**Fix:** Use **asynchronous calls** with `go` and proper error handling.
```go
// ❌ BAD: Blocking in Goroutine
go client.GetData(ctx) // Deadlock if not awaited

// ✅ GOOD: Async with error handling
done := make(chan struct{})
go func() {
    _, err := client.GetData(ctx)
    if err != nil {
        log.Printf("RPC failed: %v", err)
    }
    close(done)
}()
<-done // Wait for completion (if needed)
```

**Alternative:** Use **`grpc.WaitForReady`** for connection checks.

---

### **4. Anti-Pattern: No Connection Pooling**
**Problem:** Opening a **new gRPC connection per request** wastes resources.

**Symptoms:**
- High **connection overhead** (TLS handshakes, DNS lookups)
- **Thundering Herd** (sudden spikes in load)

**Fix:** Use **connection pooling** with `grpc.WithDefaultServiceConfig`.
```go
// Reusable connection pool
var conn *grpc.ClientConn
once := sync.Once{}
func getClientConn() (*grpc.ClientConn, error) {
    once.Do(func() {
        var err error
        conn, err = grpc.Dial(
            "example.com:50051",
            grpc.WithDefaultServiceConfig(`{
                "loadBalancingPolicy": "round_robin"
            }`),
        )
        if err != nil { panic(err) }
    })
    return conn, nil
}
```

**For load balancing:**
```go
// Enable pick-first load balancing
clientConn, err := grpc.Dial(
    "example.com:50051",
    grpc.WithDefaultServiceConfig(`{
        "loadBalancingPolicy": "pick_first"
    }`),
)
```

---

### **5. Anti-Pattern: No Retries for Transient Errors**
**Problem:** Failing **only once** on network issues (e.g., timeouts, retries).

**Symptoms:**
- **Increased 5xx errors** (due to failed retries)
- **User-facing timeouts**

**Fix:** Use **exponential backoff retries**.
```go
// Go client with retry logic
client := grpc.NewClient(
    getClientConn(),
    grpc.WithUnaryInterceptor(func(ctx context.Context, method string, req, reply interface{}, cc *grpc.ClientConn, invoker grpc.UnaryInvoker, opts ...grpc.CallOption) error {
        return invoker(ctx, method, req, reply, cc, append(opts, grpc.WaitForReady(true))...)
    }),
    grpc.WithCodecRegistry(registry.DefaultCodecRegistry()),
)
```

**Better:** Use a **circuit breaker** (e.g., `gommon/circuitbreaker`).
```go
import "github.com/avast/retry-go"

err := retry.Do(
    func() error {
        _, err := client.GetData(ctx)
        return err
    },
    retry.OnRetry(func(n uint, err error) {
        log.Printf("Retry %d failed: %v", n, err)
    }),
    retry.DelayType(retry.FixedDelay),
    retry.Delay(100*time.Millisecond),
    retry.Attempts(3),
)
```

---

### **6. Anti-Pattern: Improper Stream Handling (Buffering Issues)**
**Problem:** **Unbounded buffers** cause **OOM errors** or **high latency**.

**Symptoms:**
- `error: "stream closed"`
- **Memory spikes** in logs
- **Timeouts** due to large payloads

**Fix:** Limit stream **buffer size** and **close early**.
```go
// Server: Set max receive message size
grpc_server := grpc.NewServer(
    grpc.MaxRecvMsgSize(1<<20), // 1MB limit
    grpc.MaxSendMsgSize(1<<20),
)

// Client: Use streaming with chunks
stream, err := client.StreamData(ctx)
if err != nil { ... }
for {
    _, err := stream.Recv()
    if err == io.EOF { break }
    if err != nil { ... }
    // Process in chunks
}
```

**For bidirectional streams:**
```go
// Client: Send chunks in small batches
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
stream, err := client.BiStream(ctx)
if err != nil { ... }
go func() {
    for _, data := range chunkedData {
        err := stream.Send(&data)
        if err != nil { break }
    }
    stream.CloseSend() // Explicit close
}()
```

---

## **3. Debugging Tools & Techniques**

### **A. gRPC Logging & Tracing**
- **Enable gRPC logging:**
  ```bash
  GRPC_GO_LOG_SEVERITY_LEVEL=info ./your-app
  ```
- **Use OpenTelemetry for tracing:**
  ```go
  import "go.opentelemetry.io/otel/trace"

  tr := trace.NewTracerProvider()
  otel.SetTracerProvider(tr)
  ```

### **B. Network Debugging**
- **Check connection stats:**
  ```bash
  netstat -tulnp | grep 50051
  ```
- **Use `tcpdump` for packet inspection:**
  ```bash
  sudo tcpdump -i any -w grpc_traffic.pcap port 50051
  ```

### **C. Profiling & Benchmarking**
- **Use `pprof` to detect bottlenecks:**
  ```go
  import _ "net/http/_test"
  http.ListenAndServe(":6060", nil) // Access http://localhost:6060/debug/pprof/
  ```
- **Benchmark RPC calls:**
  ```bash
  ab -n 1000 -c 100 http://localhost:50051/your-service
  ```

### **D. gRPC-Go Specific Tools**
- **`grpcurl` (for querying gRPC services):**
  ```bash
  grpcurl -plaintext localhost:50051 list
  grpcurl -plaintext localhost:50051 describe YourService
  ```
- **`grpc_health_probe` (for health checks):**
  ```go
  healthCheck := health.NewServer()
  grpc_server.RegisterService(healthCheck)
  ```

---

## **4. Prevention Strategies**

| **Anti-Pattern**               | **Prevention** |
|---------------------------------|----------------|
| **Large payloads**             | Use compression (`gzip`), chunking, or CDN |
| **Unclosed streams**           | Always `defer` `Close()` or `CloseSend()` |
| **Blocking calls in Goroutines** | Use `go` + `context` for async calls |
| **No connection pooling**      | Reuse `grpc.ClientConn` with `WithDefaultServiceConfig` |
| **No retries for transient errors** | Use `retry-go` or `gommon/circuitbreaker` |
| **Buffering issues**           | Set `MaxRecvMsgSize`, `MaxSendMsgSize` |
| **No load balancing**           | Use `round_robin`, `pick_first`, or `least_conn` |
| **No TLS reusing**             | Use `grpc.WithTransportCredentials` with reuse |
| **No cancellations**            | Always pass `context` to RPC calls |

### **Best Practices Checklist**
✅ **Enable compression** (`gzip` for large responses)
✅ **Set message size limits** (`MaxRecvMsgSize`, `MaxSendMsgSize`)
✅ **Use connection pooling** (`WithDefaultServiceConfig`)
✅ **Implement retries with backoff**
✅ **Close streams explicitly** (`defer`, `CloseSend()`)
✅ **Use async patterns** (`go` + `context`)
✅ **Monitor connection leaks** (`grpc.ClientConn.GetState()`)
✅ **Log errors with OpenTelemetry**
✅ **Benchmark under load** (`ab`, `wrk`)

---

## **Conclusion**
gRPC anti-patterns can silently degrade performance and stability. By following structured debugging (checking logs, profiling, and enforcing best practices), you can **prevent common pitfalls** and ensure **scalable, efficient gRPC systems**.

**Final Debugging Flow:**
1. **Check logs** (`grpc-go` logs, OpenTelemetry)
2. **Profile** (`pprof`, `netstat`)
3. **Test with `grpcurl` and `ab`**
4. **Fix anti-patterns** (compression, retries, streaming)
5. **Prevent recurrence** (code reviews, CI checks)

By applying these strategies, you’ll keep gRPC-based systems **fast, reliable, and maintainable**. 🚀