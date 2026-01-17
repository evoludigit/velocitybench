---
**[Pattern] Elixir Language Patterns Reference Guide**
---

### **Overview**
Elixir’s functional, concurrent, and immutable nature enables expressive, maintainable patterns for solving distributed, concurrent, or complex stateful problems. This guide covers idiomatic Elixir patterns—**Processes, GenServers, OTP Behaviours, Error Handling, Pattern Matching, and Metaprogramming**—along with their trade-offs, best practices, and common pitfalls. Each pattern leverages Eliir’s runtime (BEAM) and ETS/Distributed features for scalability.

---

---

## **1. Schema Reference (Key Patterns)**

| **Pattern**               | **Use Case**                                                                 | **Behavioral Module**               | **Key Functions/Attributes**                                                                 | **Trade-offs**                                                                 |
|---------------------------|------------------------------------------------------------------------------|--------------------------------------|-------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Processes**             | Lightweight actors for concurrency (1:1 mapping to BEAM processes).          | `Process`                            | `spawn(fn -> ... end)`, `send(Pid, message)`, `receive`/`after`/`for`                   | Overhead for small tasks; no built-in fault tolerance.                          |
| **GenServer**             | Stateful, fault-tolerant service with lifecycle hooks.                      | `GenServer`                          | `:start_link`, `handle_call/3`, `handle_cast/2`, `init/1`, `stop/1`, `handle_info/2`       | Boilerplate for simple cases; best for structured state management.              |
| **Supervisors**           | Hierarchical process monitoring with restart strategies.                     | `Supervisor`                         | `:start_link`, `child_spec/1`, `init/1`, `start_child/2`, `restart/2`                   | Complex configuration; overkill for stateless systems.                           |
| **Applications**          | Bundling OTP Behaviours, config, and dependencies.                           | `Application`                        | `start/2` (OTP), config in `mix.exs`, `eapp` files                                     | Adds runtime complexity; useful for large-scale apps.                            |
| **Error Handling**        | Graceful recovery with `try/catch`, `:error_logger`, and `libinject`.        | `ErrorLogger` (stdlib), `libinject` | `Kernel.raise/1`, `Process.flag(:trap_exit, true)`, `Libinject.inject/2`                | Overuse can mask bugs; `raise` vs. `exit` requires careful handling.              |
| **Pattern Matching**      | Deconstructing data with guards, destructuring, and regex.                  | N/A (built-in)                       | `case`, `with`, `%{key: value}`, `~p/pattern/` (Regex), `Enum.match/2`                  | Performance overhead for large data; misleading matches can cause runtime errors. |
| **Metaprogramming**       | Dynamic code generation with macros (`__using__`, `defmodule`, `Macro.expand`).| `Code`, `Macro`                      | `defmacro`, `Macro.expand`, `Macro.alias`, `Code.eval_string/2`                          | Debugging challenges; can obscure intent.                                         |

---

---

## **2. Implementation Details**

### **2.1 Processes**
- **Concept**: Each process has a unique PID, runs a continuous loop via `receive`, and handles messages asynchronously.
- **Example**:
  ```elixir
  spawn(fn ->
    receive do
      {:ping, from} -> send(from, {:pong, from})
    end
  end)
  ```
- **Key Functions**:
  - `Process.send(Pid, message)`: Asynchronous message.
  - `Process.send_after(Pid, message, delay)`: Delayed message.
  - `Process.alive?(Pid)`: Check if process is running.
- **Pitfalls**:
  - Unhandled messages accumulate in the mailbox (`Process.get_email/1`).
  - No built-in backpressure; use `Process.monitor` + `:heart` for cleanup.

### **2.2 GenServers**
- **Concept**: A stateful actor with lifecycle hooks (start/stop/restart) and message types (`call`, `cast`).
- **Example**:
  ```elixir
  defmodule Counter do
    use GenServer

    def start_link(_) do
      GenServer.start_link(__MODULE__, :ok, name: __MODULE__)
    end

    def handle_call(:increment, _from, state) do
      {:reply, state + 1, state}
    end
  end
  ```
- **Key Functions**:
  - `GenServer.call(Pid, request, timeout)`: Synchronous (`reply` required).
  - `GenServer.cast(Pid, message)`: Asynchronous (`handle_cast`).
  - `GenServer.info/1`: Process health checks (`status`, `state`).
- **Pitfalls**:
  - Overuse of `handle_call` for async work (use `Task.async` + `send` instead).
  - State size limits (ETS/ProcessDict for large data).

### **2.3 Supervisors**
- **Concept**: Monitor child processes and restart them based on strategies (`one_for_one`, `one_for_all`).
- **Example**:
  ```elixir
  defmodule MySupervisor do
    use Supervisor

    @impl true
    def init(_) do
      children = [
        {Counter, []},
        {Worker, []}
      ]
      Supervisor.start_link(children, strategy: :one_for_one)
    end
  end
  ```
- **Key Functions**:
  - `Supervisor.child_spec/1`: Configure restart strategy (`max_restarts`, `shutdown`).
  - `Supervisor.flag(:auto_restart, true)`: Enable auto-restart.
  - `Supervisor.terminate_child/2`: Force shutdown.
- **Pitfalls**:
  - `one_for_all` can cascade failures; prefer `one_for_one`.
  - Memory leaks if child specs aren’t cleaned up.

### **2.4 Error Handling**
- **Concept**: Use `try/catch` for runtime errors, log with `:error_logger`, and inject exceptions.
- **Example**:
  ```elixir
  try do
    File.read("nonexistent.txt")
  rescue
    File.NotFound -> :error_logger.error("File missing")
  end
  ```
- **Key Functions**:
  - `raise/1`: Terminate process (use sparingly).
  - `exit/1`: Controlled process termination.
  - `Libinject.inject/2`: Replace exceptions with custom behavior.
- **Pitfalls**:
  - Silent `raise` in callbacks can hide bugs.
  - `exit` vs. `raise`: `exit` allows recovery; `raise` is abrupt.

### **2.5 Pattern Matching**
- **Concept**: Deconstruct data with destructuring and guards.
- **Example**:
  ```elixir
  case List.first([1, 2, 3]) do
    nil -> :empty
    x when x > 1 -> :greater_than_one
  end
  ```
- **Key Functions**:
  - `~p/pattern`: Regex matching (e.g., `~p/^\d+$/`).
  - `Enum.match/2`: Filter with guards (e.g., `%{age: age} when age > 18`).
- **Pitfalls**:
  - Unmatched patterns cause runtime errors.
  - Regex performance cost for large datasets.

### **2.6 Metaprogramming**
- **Concept**: Generate code dynamically with macros.
- **Example**:
  ```elixir
  defmodule Logger do
    defmacro log(level, msg) do
      quote do
        IO.puts("#{level}: #{msg}")
      end
    end
  end
  ```
- **Key Functions**:
  - `Macro.expand/1`: Debug macro expansion.
  - `defmodule_atom/2`: Dynamically define modules.
  - `Code.require_file/1`: Load external code.
- **Pitfalls**:
  - Debugging macros requires `Macro.to_string/1`.
  - Overuse increases coupling.

---

---

## **3. Query Examples**

### **3.1 Process Communication**
```elixir
# Spawn a counter and increment it
pid = spawn(fn -> counter = 0; receive do :tick -> counter += 1 end end)
send(pid, :tick)
send(pid, :tick)
# Query state (not recommended; use GenServer instead)
flush()  # Clear mailbox
Process.get_state(pid)  # ⚠️ Avoid; use GenServer's info/1
```

### **3.2 GenServer State Management**
```elixir
# Start and query GenServer
{:ok, pid} = Counter.start_link()
GenServer.call(pid, :increment)
GenServer.call(pid, :increment)
GenServer.call(pid, :get_state)  # Returns current state
```

### **3.3 Supervisor Recovery**
```elixir
# Define a transient worker
MySupervisor.child_spec(MyWorker, [restart: :transient])

# Simulate a crash (supervisor will restart it)
MyWorker.crash!
# Worker is restarted automatically after max_restarts
```

### **3.4 Error Handling with Libinject**
```elixir
# Replace File.Reader exceptions
LibInject.inject(File.Reader, [file_not_found: :handle_missing_file])

defp handle_missing_file(_) do
  :error_logger.warn("Fallback: use a default file")
  {:ok, "default.txt"}
end

File.read("missing.txt")  # Uses handle_missing_file
```

### **3.5 Pattern Matching with Guards**
```elixir
# Filter even numbers
even_numbers = Enum.filter([1, 2, 3], fn x -> x % 2 == 0 end)
# OR with guards
even_numbers = Enum.match([1, 2, 3], &(&1 % 2 == 0))
```

---

---

## **4. Related Patterns**
| **Related Pattern**       | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Task**                  | Lightweight async tasks with callbacks.                                         | Non-stateful background work (e.g., API calls).                                 |
| **Agent**                 | Simplified state management (single process).                                  | Shared state with simple operations (e.g., counters).                          |
| **ETS/DB**                | In-memory key-value stores for distributed data.                                | Caching, leader election, or distributed state.                                |
| **CTX (Context)**         | Store process-specific data.                                                    | Temporarily attach metadata to a process.                                      |
| **Dynamic Supervision**   | Dynamically add/remove supervised processes.                                   | Pluggable components (e.g., plugins).                                         |
| **GenStage**              | Stream-based processing with backpressure.                                     | High-throughput data pipelines (e.g., logs, events).                          |

---

---
### **Best Practices**
1. **Prefer GenServer over raw Processes** for stateful logic.
2. **Use supervisors for fault tolerance**—never ignore crashes.
3. **Log errors explicitly**—avoid silent failures.
4. **Leverage pattern matching** for clean data handling (but validate inputs).
5. **Limit metaprogramming**—keep macros focused on domain-specific logic.

### **Anti-Patterns**
- **Busy-waiting**: Use `receive` with timeouts or `Task.async`.
- **Global state**: Use message passing or `Agent`/`ETS`.
- **Ignoring errors**: Always handle exceptions or log them.
- **Overusing `raise`**: Prefer `exit` for controllable flow.
- **Complex macros**: Keep them simple; document their side effects.