# **[Pattern] Rust Language Patterns – Reference Guide**

---

## **Overview**
This guide provides a structured reference for Rust language patterns, covering idiomatic constructs, best practices, and anti-patterns. Rust’s strong type system, ownership model, and compiler-driven safety enforce patterns that improve code correctness, performance, and maintainability.

Key topics include:
- **Ownership and Borrowing** (slicing, references, lifetimes)
- **Error Handling** (Result, Option, custom error types)
- **Concurrency** (threads, async/await, Send/Sync traits)
- **Generics and Traits** (type bounds, trait objects)
- **Macros & Meta-Programming** (declare, derive, procedural macros)
- **Memory Safety** (unsafe blocks, raw pointers, FFI)
- **Performance Patterns** (zero-cost abstractions, iterator patterns)

Each section balances theory with practical examples. Use this as a quick lookup for common or advanced Rust constructs.

---

## **Schema Reference**
Below are core Rust patterns, categorized by domain. *Example implementations* follow each table.

| **Pattern Category**       | **Pattern Name**               | **Key Concepts**                                                                 | **Use Case**                          |
|-----------------------------|--------------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **Ownership & Borrowing**   | **Borrowing and Lifetimes**    | `&T`, `&mut T`, lifetime annotations (`'a`), `'static`                          | Safe, shared access to data.          |
|                             | **Ownership Transfer**         | `move` keyword, `Box<T>`, `Rc<T>`/`Arc<T>`, interior mutability (`Cell`, `RefCell`) | Managing move semantics and shared ownership. |
| **Error Handling**          | **Result Pattern**             | `Ok(T)`, `Err(E)`, `?` operator, `match`/`if let`                              | Handling recoverable failures.       |
|                             | **Option Pattern**             | `Some(T)`, `None`, `unwrap_or_else`, `unwrap_or_default`                       | Handling nullable/optional values.   |
|                             | **Custom Errors**              | `#[derive(Debug)]`, `thiserror`/`anyhow`, `Display`/`Error` traits            | Domain-specific error types.         |
| **Concurrency**             | **Thread Safety**              | `Send`/`Sync` traits, `Mutex<T>`, `RwLock<T>`, `Arc<Mutex<T>>`                 | Cross-thread data sharing.           |
|                             | **Async/Rust**                 | `Future`, `async/await`, `tokio`, `async_std`                                  | Non-blocking I/O and parallelism.    |
| **Generics & Traits**       | **Trait Bounds**               | `T: Clone`, `T: PartialEq + Debug`, `where` clauses                           | Constraining generic types.           |
|                             | **Trait Objects**              | `dyn Trait`, `Box<dyn Trait>`, `trait object safety`                           | Runtime polymorphism.                |
|                             | **Generics with Constraints**  | Bound inference, `impl Trait`, `fn<T: Clone>(t: T) -> T`                        | Flexible type handling.               |
| **Macros**                  | **Declare Macros**             | `macro_rules!`, pattern matching                                         | Code generation (e.g., `println!`).  |
|                             | **Derive Macros**              | `#[derive(Debug, Clone)]`, custom derive (e.g., `serde::Serialize`)         | Auto-implementing traits.            |
|                             | **Proc Macros**                | Attribute macros (`#[derive]`), item/tt macros                               | Compile-time transformations.        |
| **Memory Safety**           | **Unsafe Rust**                | `unsafe fn`, `transmute`, `extern "C"`, raw pointers (`*const T`)          | Low-level control (FFI, no_std).     |
|                             | **FFI Patterns**               | `extern "C"` functions, `#[no_mangle]`, `unsafe` block for C interop         | Integrating with C libraries.        |
| **Performance**             | **Iterator Patterns**          | Chaining (`iter().map().filter()`), `Iterator` trait, `fold`/`reduce`      | Efficient data processing.           |
|                             | **Zero-Cost Abstractions**     | `#[derive(Clone)]`, `Copy` types, compiler optimizations                   | High-performance abstractions.       |
| **Design Patterns**         | **Builder Pattern**            | `Builder` structs, `setter` methods, fluent APIs                            | Complex object construction.          |
|                             | **Singleton**                  | Static `lazy_static!` or `once_cell::sync::OnceCell`                         | Singleton instances.                 |
|                             | **State Pattern**              | `enum State`, `match` + state transitions                                  | State machines.                      |

---

## **Implementation Details**

### **1. Ownership and Borrowing**
#### **Borrowing and Lifetimes**
Rust enforces borrowing rules to prevent data races. Key rules:
- Any value can have **either** one mutable reference **or** any number of immutable references.
- References must always be valid (lifetimes).

**Example: Lifetime Annotations**
```rust
fn longest<'a>(s1: &'a str, s2: &'a str) -> &'a str {
    if s1.len() > s2.len() { s1 } else { s2 }
}
```
- `'a` ensures the returned reference lives as long as the shortest input.

#### **Ownership Transfer**
Use `move` to transfer ownership into a closure:
```rust
let vec = vec![1, 2, 3];
let handle = thread::spawn(move || {
    println!("{:?}", vec); // `vec` is moved here
});
```

---

### **2. Error Handling**
#### **Result Pattern**
Prefer `Result` over `Option + panic!`:
```rust
fn parse_number(s: &str) -> Result<i32, std::num::ParseIntError> {
    s.parse()
}
```
- Use `?` to propagate errors:
  ```rust
  fn process(s: &str) -> Result<(), Box<dyn std::error::Error>> {
      let num = parse_number(s)?; // Unwraps or propagates
      Ok(())
  }
  ```

#### **Custom Errors**
```rust
#[derive(Debug)]
struct ConfigError {
    details: String,
}

impl std::fmt::Display for ConfigError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{}", self.details)
    }
}

impl std::error::Error for ConfigError {}
```

---

### **3. Concurrency**
#### **Thread Safety**
Ensure types implement `Send` (can be sent across threads) and `Sync` (can be shared):
```rust
use std::sync::Mutex;
use std::sync::Arc; // Atomic reference counting

fn thread_safe_example() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        }));
    }

    for handle in handles {
        handle.join().unwrap();
    }
    println!("Final count: {}", *counter.lock().unwrap());
}
```

#### **Async/Rust**
```rust
use tokio::time::{sleep, Duration};

async fn fetch_data() -> Result<String, std::io::Error> {
    sleep(Duration::from_secs(1)).await;
    Ok("data".to_string())
}

#[tokio::main]
async fn main() {
    let data = fetch_data().await.expect("Failed to fetch");
    println!("{}", data);
}
```

---

### **4. Generics and Traits**
#### **Trait Bounds**
```rust
fn print_sum<T: std::fmt::Display + PartialEq>(a: T, b: T) {
    println!("Sum: {}", a + b); // Requires `Display` + `PartialEq`
}
```

#### **Trait Objects**
```rust
trait Draw {
    fn draw(&self);
}

let shapes: Vec<Box<dyn Draw>> = vec![
    Box::new(Circle { radius: 1.0 }),
    Box::new(Square { side: 1.0 }),
];
```

---

### **5. Macros**
#### **Declare Macros**
```rust
macro_rules! debug_print {
    ($val:expr) => {
        println!("{:?}", $val);
    };
}
debug_print!(vec![1, 2, 3]); // Outputs: [1, 2, 3]
```

#### **Proc Macro Example (`derive`)**
Create a `#[derive(MyTrait)]` macro:
1. Add to `Cargo.toml`:
   ```toml
   [lib]
   proc-macro = true
   ```
2. Implement `proc_macro::DeriveInput`:
   ```rust
   use proc_macro::TokenStream;
   use quote::quote;
   use syn::{parse_macro_input, DeriveInput};

   #[proc_macro_derive(MyTrait)]
   pub fn my_trait_derive(input: TokenStream) -> TokenStream {
       let input = parse_macro_input!(input as DeriveInput);
       let name = input.ident;
       let expanded = quote! {
           impl MyTrait for #name {
               fn my_method(&self) {
                   println!("{} implements MyTrait!", stringify!(#name));
               }
           }
       };
       TokenStream::from(expanded)
   }
   ```

---

### **6. Unsafe Rust**
#### **Raw Pointers**
```rust
unsafe {
    let mut num = 42 as *mut i32;
    *num = 100; // Dereference and write
}
```
- Always validate pointers:
  ```rust
  assert!(!num.is_null());
  ```

#### **FFI Example**
```rust
extern "C" {
    fn c_function(arg: i32) -> i32;
}

#[no_mangle]
pub extern "C" fn rust_function(arg: i32) -> i32 {
    unsafe { c_function(arg) }
}
```

---

### **7. Performance Patterns**
#### **Iterator Patterns**
```rust
let numbers = vec![1, 2, 3, 4];
let doubled: Vec<_> = numbers
    .into_iter()
    .map(|x| x * 2)
    .filter(|&x| x % 3 != 0)
    .collect();
```

#### **Zero-Cost Abstractions**
```rust
#[derive(Clone)] // Zero-cost clone
struct Point { x: i32, y: i32 }
```

---

## **Query Examples**
### **How do I handle large structs efficiently?**
Use **lazy initialization** (`once_cell` or `lazy_static`) or **interior mutability** (`Mutex`/`RwLock`):
```rust
use once_cell::sync::Lazy;
use std::collections::HashMap;

static COUNTRY_DB: Lazy<HashMap<String, String>> = Lazy::new(|| {
    let mut m = HashMap::new();
    m.insert("USA".to_string(), "Washington".to_string());
    m
});
```

### **How do I implement async I/O without blocking?**
Use `tokio` or `async-std`:
```rust
use tokio::fs::read_to_string;

#[tokio::main]
async fn main() {
    let content = read_to_string("file.txt").await.unwrap();
}
```

### **How do I create a thread-safe singleton?**
```rust
use once_cell::sync::OnceCell;

static SINGLETON: OnceCell<Vec<i32>> = OnceCell::new();

fn get_singleton() -> &'static mut Vec<i32> {
    SINGLETON.get_or_init(|| Vec::new())
}
```

---

## **Related Patterns**
1. **[Zero-Cost Abstractions](link)** – Ensure performance-critical code doesn’t incur runtime overhead.
2. **[Ownership Semantics](link)** – Master Rust’s borrow checker for safe memory management.
3. **[Async Runtime Design](link)** – Structure async applications with `tokio` or `async-std`.
4. **[FFI Guidelines](link)** – Safely integrate with C libraries using `extern "C"`.
5. **[Iterator Adaptors](link)** – Chain operations like `map`, `filter`, `fold` for functional-style code.