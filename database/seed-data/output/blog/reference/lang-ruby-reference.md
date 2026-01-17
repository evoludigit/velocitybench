---
# **[Ruby Language Patterns] Reference Guide**

---

## **Overview**
The **Ruby Language Patterns** reference guide documents idiomatic, reusable, and best-practice techniques for writing clean, efficient, and maintainable Ruby code. Ruby’s dynamic nature, metaprogramming capabilities, and expressive syntax enable powerful patterns—ranging from **block-based iterations** and **monkey-patching** to **meta-programming hacks** and **idiomatic object design**. This guide categorizes these patterns by use case, provides implementation details, highlights trade-offs, and includes real-world examples. Whether you're optimizing performance, improving readability, or leveraging Ruby’s metaprogramming, this reference ensures you apply the right tool for the job without falling into anti-patterns.

---

## **Schema Reference**
Below are core Ruby patterns categorized by purpose, along with their **key attributes**, **use cases**, and **anti-patterns**.

| **Pattern**               | **Purpose**                                      | **Key Attributes**                                                                 | **Use Cases**                                                                 | **Anti-Patterns/Trade-offs**                                                                 |
|---------------------------|--------------------------------------------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Blocks & Procs**        | Functional-style iteration                    | - Anonymous methods (lambdas, procs, methods)                                     | - Loops (`each`, `map`, `select`)                                               | Overusing blocks for side effects. Inline blocks reduce readability.                             |
| **Symbol Lookup (`send`)**| Dynamic method invocation                       | - `method(`), `send`, `public_send`                                                | - Dynamic feature flags, plugin systems                                           | Misuse can lead to `NoMethodError` risks. Prefer explicit methods where possible.             |
| **Monkey Patching**       | Extending existing classes                      | - `class << obj; def method; end`                                                 | - Legacy code refactoring, DSLs                                                   | Overuse can break encapsulation. Test thoroughly.                                           |
| **Method Chaining**       | Fluent API design                              | - Returning `self` in methods                                                       | - DSLs (e.g., Rails queries, builder patterns)                                   | Deep chains reduce readability. Use sparingly.                                                   |
| **Singleton Pattern**     | Global singleton objects                       | - `class << self; def self.instance; end`                                         | - Configuration managers, logging singletons                                        | Tight coupling; prefer dependency injection.                                                   |
| **Module Included/Extends**| Mixin for module methods                        | - `include`, `extend`, `prepend`                                                    | - Shared behavior (e.g., `Enumerable`, custom mixins)                           | Overuse increases modularity cost. Favor composition over inheritance.                        |
| **Meta-Programming**      | Dynamic code generation                        | - `define_method`, `class_eval`, `method_missing`, `const_missing`               | - Code generation, dynamic feature toggles, plugins                               | Debugging difficulty. Use cautiously in production.                                          |
| **Lazy Evaluation**       | Deferred computation                           | - `lazy`, `Enumerator` (Ruby 2.4+)                                                  | - Large data processing, on-demand generation                                      | Memory leaks if iterators aren’t exhausted.                                                   |
| **Case Equality (`===`)** | Custom object comparison                        | - Overriding `===` for type checking/pattern matching                             | - Pattern matching (e.g., `case obj when TypeA: ...`)                            | Misuse can lead to confusing behavior. Prefer `eql?` for value equality.                     |
| **Yield vs. `call`**      | Block vs. block-like methods                   | - `yield` (blocks), `call` (procs)                                                 | - Blocks for iteration, procs for reusability                                     | `yield` is slower; `call` is explicit. Choose based on control flow needs.                     |
| **Lazy Attributes**       | On-demand computation                          | - `attr_reader` + lazy initialization                                              | - Expensive computations (e.g., caching)                                          | Race conditions if not thread-safe. Use `Mutex` if needed.                                   |
| **Type Checking**         | Runtime type safety                            | - `TypeError`, `valid_type?`, `respond_to?`                                         | - Safe method calls, plugin validation                                            | Overhead in dynamic languages. Balance with flexibility.                                      |
| **Kernel Methods**        | Common utilities                               | - `tap`, `with_object`, `method`, `send`, `instance_eval`                          | - Chaining, meta-programming, DSLs                                                 | Excessive use reduces readability. Prefer explicit methods.                                   |
| **Regex & Symbol Matching**| Pattern matching with symbols                  | - `Symbol#to_proc`, regex with `match_data`                                        | - DSLs, query builders                                                          | Complex regexes are hard to maintain. Prefer explicit logic.                                 |
| **Thread Safety**         | Concurrent-safe code                            | - `Mutex`, `Monitor` (Ruby 2.7+), `Thread`                                       | - Shared resource access                                                         | Overhead in single-threaded apps. Use only when necessary.                                    |
| **Freezing Objects**      | Immutable objects                              | - `freeze` (frozen classes/strings)                                               | - Security-critical data (e.g., config)                                           | `freeze` breaks inheritance/method modification. Use carefully.                               |
| **Symbolized Keys**       | Hash key consistency                           | - `%i[]`, `to_sym`, `symbolize_keys`                                               | - API responses, configuration hash normalization                                  | Performance overhead for large hashes. Prefer string keys if type safety isn’t needed.       |
| **Singleton Class Methods** | Module-level singletons                      | - `class << self` + `def self.method`                                              | - Configuration or helper methods                                                 | Can shadow instance methods. Use sparingly.                                                 |
| **Lazy Loaders**          | Deferred object initialization                  | - `lazy` (Ruby 2.4+), `lazy { ... }`                                               | - Heavy dependencies, lazy initialization                                         | Memory leaks if not garbage-collected.                                                     |
| **Custom Prefixes**       | Method name filtering                          | - `method_missing` + `private_methods`                                           | - Custom DSLs (e.g., `scope` in Rails)                                            | Debugging complexity. Document clearly.                                                     |

---

## **Query Examples**
Practical implementations of Ruby patterns with edge cases and optimizations.

---

### **1. Blocks & Procs**
#### **Basic Iteration with `each`**
```ruby
[1, 2, 3].each { |x| puts x }  # Standard block
[1, 2, 3].each do |x|
  puts x
end
```
#### **Lambda vs. Proc**
```ruby
# Lambda (strict arity)
lambda { |x| x + 1 }.call(2)       # => 3
# Proc (flexible arity)
proc { |x| x + 1 }.call(2, 3)    # => 5 (ignores extra args)

# Key difference: Lambda raises `ArgumentError` for wrong args.
```

#### **Block as Last Argument**
```ruby
def process(*args, &block)
  args.each(&block)  # Pass block directly
end

process(1, 2) { |x| puts x }
```

---

### **2. Dynamic Method Invocation (`send`)**
#### **Safe vs. Unsafe `send`**
```ruby
# Unsafe (raises NoMethodError)
obj.send(:nonexistent_method)

# Safe (returns nil)
obj.send(:nonexistent_method, "default") || "fallback"
# Or:
obj.method(:nonexistent_method).call("default") rescue "fallback"
```

#### **Dynamic Method Generation**
```ruby
def dynamic_method(name)
  define_method(name) { puts "#{name} called!" }
end

class Test
  dynamic_method :hello
end

obj = Test.new
obj.hello  # => "hello called!"
```

---

### **3. Monkey Patching**
#### **Extending `String`**
```ruby
class String
  def reverse_words
    reverse.split.reverse.join(" ")
  end
end

"hello world".reverse_words  # => "world hello"
```
**Warning:** Avoid patching core classes in production.

---

### **4. Method Chaining**
#### **Fluent Builder Pattern**
```ruby
class QueryBuilder
  def where(condition)
    @conditions ||= []
    @conditions << condition
    self
  end

  def limit(n)
    @limit = n
    self
  end
end

QueryBuilder.new.where("id > 0").limit(10)
```

---

### **5. Lazy Evaluation**
#### **Lazy Array**
```ruby
lazy_array = (1..1_000_000).lazy.map { |x| x * 2 }
lazy_array.take(5).to_a  # => [2, 4, 6, 8, 10] (doesn’t compute full array)
```

---

### **6. Meta-Programming**
#### **Dynamic `method_missing`**
```ruby
class Dynamic
  def method_missing(name, *args)
    puts "Called #{name} with #{args}"
  end
end

obj = Dynamic.new
obj.nonexistent_method("test")  # => "Called nonexistent_method with ["test"]"
```

#### **`const_missing` for Plugins**
```ruby
module Plugins
  def const_missing(name)
    require_relative "plugins/#{name.downcase}.rb"
    const_get(name)
  rescue LoadError
    nil
  end
end

Plugins.const_get(:UserAuth)  # Loads "plugins/user_auth.rb"
```

---

### **7. Thread Safety**
#### **Mutex Example**
```ruby
mutex = Mutex.new
shared_counter = 0

10.times do |i|
  Thread.new do
    mutex.synchronize { shared_counter += 1 }
  end
end.join

puts shared_counter  # => 10 (thread-safe)
```

---

### **8. Type Checking**
#### **Safe Method Call**
```ruby
def safe_call(obj, method, *args)
  obj.respond_to?(method) ? obj.send(method, *args) : nil
end

safe_call(user, :name)  # => nil if user has no `name` method
```

---

### **9. Symbolized Keys**
#### **Normalizing Hash Keys**
```ruby
{ "id" => 1, :name => "Alice" }.symbolize_keys
# => {:id=>1, :name=>"Alice"}

# Or:
hash = { "id" => 1 }
hash.transform_keys(&:to_sym)
```

---

## **Related Patterns**
To complement **Ruby Language Patterns**, consider these related designs:

1. **[Object Composition]**
   - Use composition over inheritance for flexible, maintainable code.
   - Example: Delegators (`Delegator.new`) for lightweight wrappers.

2. **[Dependency Injection]**
   - Decouple dependencies via constructors or `OpenStruct`.
   - Example: `require 'ostruct'; config = OpenStruct.new(id: 1)`.

3. **[Active Record Pattern]**
   - Ruby’s ORM patterns (e.g., Rails’ `has_many`, `belongs_to`).
   - Example:
     ```ruby
     class Post < ApplicationRecord
       has_many :comments
     end
     ```

4. **[Singleton Pattern]**
   - Global state management (avoid in favor of DI where possible).
   - Example:
     ```ruby
     class Database
       @@instance = nil
       def self.instance
         @@instance ||= new
       end
     end
     ```

5. **[Builder Pattern]**
   - Construct complex objects step-by-step (e.g., Nokogiri::XML::Builder).
   - Example:
     ```ruby
     builder = Nokogiri::XML::Builder.new { |xml| xml.user { xml.name "Alice" } }
     ```

6. **[Strategy Pattern]**
   - Dynamic algorithms via blocks or modules.
   - Example:
     ```ruby
     module SortStrategies
       def self.call(array, &block)
         array.sort(&block)
       end
     end

     SortStrategies.call([3, 1, 2]) { |a, b| a <=> b }
     ```

7. **[Observer Pattern]**
   - Event notifications with `Observer` or Pub/Sub.
   - Example (using `observer` gem):
     ```ruby
     class User < ActiveRecord::Base
       has_many :observers, class_name: "Observer"
     end
     ```

8. **[Plugin Pattern]**
   - Extensible systems via `const_missing` or `require` hooks.
   - Example:
     ```ruby
     module Extensions
       def self.included(base)
         base.extend(ClassMethods)
       end

       module ClassMethods
         def custom_method; puts "Extended!" end
       end
     end

     class MyClass
       include Extensions
     end
     ```

---

## **Best Practices & Pitfalls**
### **✅ Best Practices**
1. **Prefer Explicit Over Dynamic**
   - Use `send` sparingly; prefer explicit method calls for readability.
   - Example: `obj.foo` > `obj.send(:foo)`.

2. **Document Meta-Programming**
   - Clearly document dynamic methods (e.g., `method_missing`) in class docs.

3. **Thread Safety First**
   - Assume concurrency unless working in single-threaded contexts.

4. **Avoid Global State**
   - Prefer dependency injection over singletons or class variables.

5. **Optimize Lazy Evaluation**
   - Use `lazy` for large datasets but ensure iterators are consumed (e.g., `.to_a`).

6. **Test Edge Cases**
   - Test `method_missing`, `const_missing`, and dynamic features thoroughly.

### **❌ Anti-Patterns**
1. **Over-Monkey-Patching**
   - Patching core classes (e.g., `Array`, `Hash`) in production breaks predictability.

2. **Unbounded Lazy Iterators**
   - Forgetting to consume lazy enumerators leaks memory:
     ```ruby
     # Bad: Iterators may not be exhausted.
     (1..1_000_000).lazy.map { |x| x * 2 }.to_a  # Good
     # Bad:
     (1..1_000_000).lazy.map { |x| x * 2 }  # Memory leak!
     ```

3. **Blocking in Background Threads**
   - Avoid blocking threads in long-running operations (use `async` gems like `sidekiq`).

4. **Ignoring `method_missing`**
   - Unhandled `method_missing` can crash apps silently.

5. **Deep Method Chaining**
   - Chains > 3 methods reduce readability:
     ```ruby
     # Bad
     user.profile.address.city

     # Better
     user.profile.address.city
     # Or:
     address = user.profile.address
     address.city
     ```

6. **Freezing Critical Objects**
   - `freeze` breaks inheritance and can cause `FrozenError` crashes.

---

## **Performance Considerations**
| **Pattern**               | **Performance Impact**                                                                 | **Optimization Tips**                                                                 |
|---------------------------|----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **`send`/`method`**       | Slightly slower than direct calls (~10-20% overhead).                                   | Cache methods if used repeatedly (e.g., `cache = obj.method(:foo)`).                 |
| **Blocks**                | Lambdas/procs have minimal overhead; blocks are optimized in loops.                   | Prefer `map`/`select` over iterative blocks for large datasets.                        |
| **Meta-Programming**      | Compile-time overhead for `define_method`.                                             | Use `class_eval` sparingly; prefer `extend` for modules.                              |
| **Lazy Evaluation**       | Reduces memory usage but adds per-element overhead.                                   | Use when processing unbounded data (e.g., streams).                                   |
| **Threading**             | `Mutex` adds lock contention; `Thread` has per-thread overhead.                       | Use `Concurrent::Ruby` for thread pools or `fork` for CPU-bound tasks.                |
| **Symbol Lookup**         | `===` and `method_missing` have hash/map overhead.                                    | Prefer explicit methods for hot paths.                                               |

---
## **Further Reading**
- **Official Docs**:
  - [Ruby Core Guide](https://ruby-doc.org/core-3.1/)
  - [Metaprogramming Ruby](https://metaprogramming.rubyforge.org/)
- **Books**:
  - *The Well-Grounded Rubyist* (David Blackwell) – Covers idiomatic Ruby.
  - *Practical Object-Oriented Design in Ruby* (Sandi Metz) – Design patterns.
- **Gems**:
  - [`activerecord`](https://github.com/rails/rails) (for ORM patterns).
  - [`observer`](https://github.com/collectiveidea/observer) (pub/sub).
  - [`lazy`](https://github.com/rails/lazy) (for lazy evaluation).
- **Tools**:
  - `ruby-prof` for benchmarking metaprogramming overhead.
  - `simplecov` to verify code coverage in dynamic features.