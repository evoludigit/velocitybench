# **[Go Language Patterns] Reference Guide**

---

## **Overview**
The **Go Language Patterns** reference guide provides a structured approach to writing idiomatic, efficient, and maintainable Go code. This documentation covers core Go design principles, common patterns, implementation best practices, and anti-patterns. Whether you're working on microservices, CLI tools, or concurrent systems, understanding these patterns ensures scalable, performant, and clean architecture.

Key themes include:
- **Concurrency & Parallelism** (goroutines, channels, sync primitives)
- **Error Handling** (context-based, custom types)
- **Dependency Management** (composition, dependency injection)
- **Interfacing & Polymorphism** (embedding, interfaces)
- **Memory & Performance** (zero allocation, pointer usage)
- **Testing & Observability** (mocking, logging, metrics)

This guide is designed for intermediate to advanced Go developers seeking to deepen their expertise.

---

## **Schema Reference**
Below are essential Go patterns categorized by application area. Each entry includes a **description**, **use case**, **code example**, and **key considerations**.

| **Pattern Name**               | **Description**                                                                 | **Use Case**                                                                 | **Key Considerations**                                                                 |
|--------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Goroutine Pool**            | Limits concurrent goroutines to prevent resource exhaustion.                   | CPU-bound or I/O-heavy workloads (e.g., batch processing).                    | Monitor goroutine counts with `runtime.GOMAXPROCS`.                                    |
| **Context Cancellation**      | Propagates cancellation signals across goroutines.                           | Time-sensitive operations (e.g., HTTP requests, long-running tasks).         | Always check `Cancel()` and `Done()` to avoid leaks.                                |
| **Struct Embedding**          | Uses `struct` embedding to achieve method inheritance.                      | Implementing common interfaces (e.g., `io.Reader`, `io.Writer`).              | Avoid deep embedding to prevent ambiguity.                                           |
| **Error Wrapping**            | Uses `fmt.Errorf` with `%w` to chain errors for better debugging.             | Resource recovery (e.g., DB operations with retries).                          | Use `%w` instead of `%v` to preserve stack traces.                                    |
| **Factory Functions**         | Centralizes object creation to ensure consistency.                           | Dependency-heavy applications (e.g., configuration management).              | Prefer `NewFoo()` over `foo{}` constructors for clarity.                              |
| **Channel Buffering**         | Uses buffered channels to limit buffering overhead.                          | Producer-consumer scenarios (e.g., task queues).                            | Buffer size should match expected workload (e.g., `make(chan T, 10)`).                 |
| **Select with Timeout**       | Combines `select` with `context` for timeout handling.                       | API calls with graceful degradation.                                           | Avoid busy-waiting by using `select` instead of `time.Sleep`.                         |
| **Interface Composition**     | Combines interfaces to enforce multiple behaviors.                           | Polymorphic systems (e.g., logging with `io.Writer` + `io.Closer`).          | Document the expected behavior of each interface.                                    |
| **Zero-Allocation Slicing**   | Reuses pre-allocated slices to avoid GC pressure.                            | High-performance loops (e.g., batch processing).                            | Pre-allocate slices with `make([]T, 0, cap)` for reuse.                               |
| **Dependency Injection**      | Passes dependencies explicitly via function parameters.                      | Modular applications (e.g., plugins, testing).                              | Avoid global state; use constructors or factories.                                   |
| **Worker Pool with Task Queue** | Uses a channel-backed task queue for workload distribution.              | Parallel processing (e.g., image resizing, data transformation).            | Dynamically adjust worker count based on load.                                       |
| **Custom Assertions**         | Wraps `testing.T` for reusable test validation.                            | Comprehensive unit testing.                                                   | Use `Require`/`Expect` to distinguish between errors and failures.                  |

---

## **Implementation Details**

### **1. Goroutine Pool**
**Implementation:**
```go
func workerPool(tasks <-chan Task, results chan<- Result, numWorkers int) {
    for i := 0; i < numWorkers; i++ {
        go func() {
            for task := range tasks {
                results <- processTask(task)
            }
        }()
    }
}
```
**Usage:**
```go
tasks := make(chan Task, 100)
results := make(chan Result, 100)
workerPool(tasks, results, 5)
```

**Key Points:**
- Limits concurrency to avoid resource starvation.
- Useful for CPU-bound tasks where `GOMAXPROCS` is a bottleneck.

---

### **2. Context Cancellation**
**Implementation:**
```go
func fetchData(ctx context.Context, url string) ([]byte, error) {
    req, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    resp, err := http.Get(url)
    if err != nil {
        return nil, fmt.Errorf("HTTP request failed: %w", err)
    }
    defer resp.Body.Close()
    return io.ReadAll(resp.Body)
}
```
**Usage:**
```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()
data, err := fetchData(ctx, "https://example.com/api")
```

**Key Points:**
- Always `defer` cancellation to prevent leaks.
- Use `context.WithTimeout` for operation timeouts.

---

### **3. Struct Embedding**
**Implementation:**
```go
type ReaderWriter struct {
    *buf io.Reader
    *bufWriter io.Writer
}

func (rw *ReaderWriter) Read(p []byte) (n int, err error) {
    return rw.buf.Read(p)
}

func (rw *ReaderWriter) Write(p []byte) (n int, err error) {
    return rw.bufWriter.Write(p)
}
```
**Usage:**
```go
rw := &ReaderWriter{
    buf:       bytes.NewBuffer([]byte("test")),
    bufWriter: bufio.NewWriter(os.Stdout),
}
io.Copy(rw, rw) // Reuses embedded methods
```

**Key Points:**
- Embedding delegates methods (no `Read()`/`Write()` defined explicitly).
- Avoid deep embedding (e.g., `type A struct { B struct { C struct {}} }`).

---

### **4. Error Wrapping**
**Implementation:**
```go
func readFile(path string) ([]byte, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("failed to read %s: %w", path, err)
    }
    return data, nil
}

func processData(data []byte) error {
    if err := validate(data); err != nil {
        return fmt.Errorf("invalid data: %w", err)
    }
    return nil
}
```
**Usage:**
```go
data, err := readFile("config.json")
if err != nil {
    logger.Fatalf("error: %v", err) // Prints full stack trace
}
```

**Key Points:**
- Use `%w` to chain errors (preserves stack traces).
- Avoid `%v` (loses context).

---

### **5. Factory Functions**
**Implementation:**
```go
type Config struct {
    DBHost string
    Port   int
}

func NewConfig(host string, port int) *Config {
    return &Config{
        DBHost: host,
        Port:   port,
    }
}
```
**Usage:**
```go
cfg := NewConfig("localhost", 8080)
```

**Key Points:**
- Encapsulates object creation logic.
- Easier to mock in tests.

---

## **Query Examples**

### **Concurrency: Worker Pool with Task Queue**
```go
// 5 workers processing tasks from a channel
workers := 5
tasks := make(chan Task, 100)
results := make(chan Result, 100)

for i := 0; i < workers; i++ {
    go func() {
        for task := range tasks {
            results <- processTask(task)
        }
    }()
}

// Feed tasks
go func() {
    for _, task := range []Task{{ID: 1}, {ID: 2}} {
        tasks <- task
    }
    close(tasks)
}()

// Collect results
for result := range results {
    fmt.Println(result)
}
```

### **Error Handling: Context with Retries**
```go
func retryOperation(ctx context.Context, op func() error, maxRetries int) error {
    var lastErr error
    for i := 0; i < maxRetries; i++ {
        if err := op(); err == nil {
            return nil
        }
        lastErr = err
        if err := ctx.Err(); err != nil {
            return fmt.Errorf("context cancelled: %w", err)
        }
        time.Sleep(time.Duration(i+1) * time.Second)
    }
    return fmt.Errorf("all retries failed: %w", lastErr)
}

// Usage
err := retryOperation(context.Background(), func() error {
    return someExpensiveOperation()
}, 3)
```

### **Interfacing: Multiple Inheritance via Interfaces**
```go
type Logger interface {
    Log(msg string)
}

type Closer interface {
    Close() error
}

type FileLogger struct{}

func (f *FileLogger) Log(msg string) {
    fmt.Println("LOG:", msg)
}

func (f *FileLogger) Close() error {
    return nil
}

func useLogger(l Logger) {
    l.Log("Hello")
}

func useCloser(c Closer) {
    c.Close()
}

// Usage
logger := &FileLogger{}
useLogger(logger)
useCloser(logger) // Satisfies both interfaces
```

---

## **Related Patterns**
1. **[Concurrency Patterns](https://pkg.go.dev/std@go1.20.0/sync)** – Advanced sync primitives (`WaitGroup`, `Mutex`).
2. **[Builder Pattern](https://refactoring.guru/design-patterns/builder)** – Step-by-step object construction (e.g., `strings.Builder`).
3. **[Singleton Pattern](https://github.com/volatiletech/null-session)** – Global state management (use sparingly).
4. **[Command Pattern](https://pkg.go.dev/github.com/jmoiron/sqlx)** – Encapsulate actions as objects (e.g., SQL queries).
5. **[Observer Pattern](https://pkg.go.dev/github.com/fsnotify/fsnotify)** – Event-driven updates (e.g., file watches).
6. **[Repository Pattern](https://github.com/go-pg/pg)** – Abstraction layer for data access.

---

## **Best Practices & Anti-Patterns**

### **Best Practices**
✅ **Use `defer`** for cleanup (files, locks, contexts).
✅ **Favor interfaces over concrete types** for flexibility.
✅ **Prefer `context` over timeouts** (`time.Sleep` is blocking).
✅ **Limit goroutine counts** to avoid memory leaks.
✅ **Document error types** (e.g., `err == io.ErrClosed`).

### **Anti-Patterns**
❌ **Global variables** – Use dependency injection.
❌ **Ignoring errors** – Always handle or propagate errors.
❌ **Overusing reflection** – Prefer interfaces for polymorphism.
❌ **Unbounded goroutines** – Leads to memory exhaustion.
❌ **Deeply nested conditionals** – Refactor with guards or polymorphism.

---
**Final Note:**
Mastering these patterns will elevate your Go code from functional to **idiomatic and production-ready**. Combine them strategically for maintainable, scalable applications. For further reading, refer to:
- [Effective Go](https://golang.org/doc/effective_go.html)
- [Go Concurrency Patterns](https://github.com/tevino/abo/wiki/Concurrency-Patterns-for-Go)
- [10 Common Go Pitfalls](https://blog.golang.org/pitfalls)