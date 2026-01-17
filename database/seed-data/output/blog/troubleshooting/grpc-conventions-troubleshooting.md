# **Debugging gRPC Conventions: A Troubleshooting Guide**

## **Introduction**
gRPC is a high-performance RPC framework that uses HTTP/2 for efficient communication. When following **gRPC Conventions** (protos, service definitions, error handling, logging, and metrics), issues can arise from misconfigurations, incorrect protobuf definitions, or runtime misbehavior. This guide provides a structured approach to diagnosing and resolving common gRPC-related problems.

---

## **1. Symptom Checklist**
Before diving into debugging, identify which symptoms match your issue:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|---------------------------------------------|
| ✅ Client-server connection refused  | Network misconfiguration, firewall blocking, incorrect host/port |
| ✅ RPC calls hanging/timeout         | Unresponsive server, deadlock, incorrect timeout settings |
| ✅ Protobuf serialization errors     | Incorrect `.proto` definitions, wrong structs |
| ✅ High latency or slow responses    | Throttling, inefficient streaming, no load balancing |
| ✅ Unexpected `STATUS_UNAVAILABLE`  | Server overloaded, misconfigured load balancer |
| ✅ `InvalidArgument` or `Unknown` errors | Invalid Protobuf fields, malformed requests |
| ✅ Memory leaks or crashes          | Poorly handled streams, unclosed connections |
| ✅ Metrics/logs show connection resets | Network instability, TLS misconfiguration |

If multiple symptoms appear, start with **network connectivity** (Symptom 1) before moving to **gRPC-specific issues**.

---

## **2. Common Issues & Fixes**

### **2.1 gRPC Connection Refused (Client-Server Issue)**
**Symptoms:**
- `grpc: address connection refused`
- `dial tcp: lookup server.example.com: no such host`

**Possible Causes & Fixes:**

#### **A. Incorrect Target Address**
- **Check:** Ensure the server URL is correct (e.g., `"address=localhost:50051"`).
- **Fix:** Verify `host:port` in client calls:
  ```go
  // Wrong: localhost is ambiguous (can be IPv4 or IPv6)
  conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())

  // Correct: Explicitly use an IP or resolve DNS first
  conn, err := grpc.Dial("127.0.0.1:50051", grpc.WithInsecure())
  ```

#### **B. Firewall or Network Blocks Port**
- **Check:** Test connectivity with `telnet` or `nc`:
  ```sh
  telnet localhost 50051  # Should return "Connection refused" (not timeout)
  ```
- **Fix:** Adjust firewall rules or check if the server is behind a proxy.

#### **C. Server Not Running or Misconfigured**
- **Check:** Verify the gRPC server is listening:
  ```sh
  netstat -tulnp | grep 50051  # (Linux)
  lsof -i :50051           # (Mac)
  ```
- **Fix:** Ensure the server is started with the correct port:
  ```go
  lis, err := net.Listen("tcp", ":50051")
  if err != nil {
      log.Fatalf("Failed to listen: %v", err)
  }
  s := grpc.NewServer()
  pb.RegisterMyServiceServer(s, &server{})
  s.Serve(lis) // Must be blocking
  ```

---

### **2.2 gRPC RPC Hang/Timeout**
**Symptoms:**
- Clients stuck waiting indefinitely.
- `context.DeadlineExceeded` or `context.Canceled`.

**Possible Causes & Fixes:**

#### **A. Server Taking Too Long**
- **Check:** Log request start/end times on the server.
- **Fix:** Implement **timeouts** on both client and server:
  ```go
  // Client: Set a 5s timeout
  ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
  defer cancel()
  _, err := client.Call(ctx, &pb.Request{})

  // Server: Use shorter processing time or async handling
  go func() {
      resp, err := longRunningOperation()
      if err != nil {
          ctx.SetValue("error", err) // Handle in client
          return
      }
      _ = s.SendAndClose(resp)
  }()
  ```

#### **B. Deadlock in Server Handler**
- **Check:** Use `pprof` to detect blocking goroutines.
- **Fix:** Avoid blocking calls in handlers. Use **workers** for CPU-bound tasks:
  ```go
  // Bad: Blocking sync call
  func (s *server) DoSomething(ctx context.Context, req *pb.Request) (*pb.Response, error) {
      time.Sleep(10 * time.Second) // Deadlock risk!
      return &pb.Response{}, nil
  }

  // Good: Offload to a goroutine
  func (s *server) DoSomething(ctx context.Context, req *pb.Request) (*pb.Response, error) {
      ch := make(chan *pb.Response)
      go func() {
          resp := computeExpensive(req)
          ch <- resp
      }()
      select {
      case <-ctx.Done():
          return nil, ctx.Err()
      case resp := <-ch:
          return resp, nil
      }
  }
  ```

---

### **2.3 Protobuf Serialization Errors**
**Symptoms:**
- `grpc: received message larger than max`
- `proto: invalid wire type`

**Possible Causes & Fixes:**

#### **A. Mismatched `.proto` Versions**
- **Check:** Ensure all services use the **same `.proto` file**.
- **Fix:** Generate code with matching protobuf compiler (`protoc`):
  ```sh
  protoc --go_out=. --go-grpc_out=. services/proto/v1/service.proto
  ```

#### **B. Invalid Fields in Request/Response**
- **Check:** Validate request data before sending:
  ```go
  if req.GetUnsetField() != nil { // Hypothetical invalid check
      return nil, status.Errorf(codes.InvalidArgument, "invalid field")
  }
  ```

#### **C. Message Size Too Large**
- **Fix:** Set a max receive size on the server:
  ```go
  s := grpc.NewServer(
      grpc.MaxRecvMsgSize(1024*1024), // 1MB limit
  )
  ```

---

### **2.4 High Latency or Slow Responses**
**Symptoms:**
- RPCs taking >1s, inconsistent response times.

**Possible Causes & Fixes:**

#### **A. Streaming Without Concurrency**
- **Fix:** Use **parallel requests** or **async processing**:
  ```go
  // Stream requests in parallel
  var wg sync.WaitGroup
  wg.Add(N)
  for i := 0; i < N; i++ {
      go func(idx int) {
          defer wg.Done()
          resp, err := client.Call(&pb.Request{Id: idx})
          // Handle response
      }(i)
  }
  wg.Wait()
  ```

#### **B. No Load Balancing**
- **Fix:** Use **client-side load balancing** (e.g., `grpc.WithBalancerName`):
  ```go
  conn, err := grpc.Dial(
      "dns:///service.example.com",
      grpc.WithBalancerName("round_robin"),
  )
  ```

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                          | **Example Command**                          |
|-------------------------|---------------------------------------|---------------------------------------------|
| **`grpc_health_probe`** | Check server liveness                | `grpcurl -plaintext localhost:50051 health.probe` |
| **`grpcurl`**           | Test RPCs without code                | `grpcurl -plaintext localhost:50051 list`   |
| **`netstat`/`ss`**      | Check open ports/connections         | `ss -tulnp | grep 50051`                                |
| **`pprof`**             | Detect goroutine leaks                | `go tool pprof http://localhost:6060/debug/pprof/goroutine` |
| **Grafana + Prometheus** | Monitor RPC metrics (latency, errors)| `grpc_server_handling_time_seconds`          |
| **`go vet`**            | Catch protobuf misconfigurations      | `protoc --go-grpc_out=. --go_opt=paths=source_relative --go_out=. service.proto` |

---

### **Key Debugging Techniques**
1. **Enable gRPC Tracing** (for distributed tracing):
   ```go
   s := grpc.NewServer(
       grpc.StatsHandler(&tracestats.Handler{}), // Jaeger integration
   )
   ```
2. **Use `grpc.TraceServer` for verbose logs**:
   ```go
   s := grpc.NewServer(grpc.TraceServer())
   ```
3. **Check Protobuf Codegen** for typos:
   ```sh
   protoc --go_out=. --go-grpc_out=. service.proto
   grep -r "undefined" ./generated/
   ```

---

## **4. Prevention Strategies**
| **Strategy**                          | **Implementation**                                                                 |
|----------------------------------------|------------------------------------------------------------------------------------|
| **Version Control `.proto` files**    | Use semantic versioning (`v1/service.proto`) and tag releases.                  |
| **Automated Protobuf Validation**     | Add `protoc` check in CI/CD.                                                      |
| **Graceful Shutdowns**                | Implement `shutdown` hook to close connections.                                   |
| **Metrics & Alerts**                  | Track `grpc_server_started_total`, `grpc_client_call_latency`.                   |
| **Client Timeout Defaults**           | Enforce timeouts globally: `grpc.WithDefaultCallOptions(grpc.WaitForReady(true))`. |
| **Schema Registry**                   | Use Google’s API Gateway or Draft for backward compatibility.                     |

---

## **5. Final Checklist Before Production**
✅ **Network:** Verify ports open (`50051`), no firewalls blocking.
✅ **Protobuf:** Match `.proto` versions across services.
✅ **Timeouts:** Set reasonable timeouts (client + server).
✅ **Concurrency:** Avoid blocking handlers; use goroutines.
✅ **Metrics:** Enable Prometheus metrics for RPCs.
✅ **Load Test:** Use `k6` or `locust` to simulate traffic.

---

## **Conclusion**
Debugging gRPC misconfigurations requires a **step-by-step approach**:
1. **Start with network connectivity** (port, firewall).
2. **Check protobuf definitions** (mismatches, size limits).
3. **Profile for deadlocks/hangs** (`pprof`, `tracing`).
4. **Monitor latency and errors** (metrics, logs).

By following this guide, you should quickly isolate and resolve most gRPC-related issues. For complex cases, leverage **distributed tracing (Jaeger/Zipkin)** and **load testing**.

---
**Further Reading:**
- [gRPC Best Practices](https://grpc.io/blog/)
- [Protobuf Schema Design](https://developers.google.com/protocol-buffers/docs/proto3)
- [gRPC Debugging with `grpcurl`](https://github.com/fullstorydev/grpcurl)