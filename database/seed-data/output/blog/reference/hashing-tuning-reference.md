# **[Pattern] Hashing Tuning Reference Guide**

---

## **Overview**
Hashing Tuning is an optimization pattern designed to improve performance in systems relying on hash-based data structures (e.g., hash tables, caches, or lookup dictionaries) by adjusting parameters like hash function granularity, collision resolution, and memory allocation. This pattern ensures optimal trade-offs between time complexity (e.g., O(1) lookups), memory usage, and scalability, especially under varying workloads. It is critical for databases, in-memory caches (e.g., Redis), distributed systems, and high-frequency trading platforms where hashing underpins key operations.

Key use cases include:
- Reducing collision overhead in hash tables.
- Balancing memory consumption vs. query speed.
- Adapting to dynamic data growth (e.g., auto-resizing).
- Mitigating hash clustering (e.g., "snowflake" or "primary clustering" issues).

---

## **Implementation Details**

### **Key Concepts**
| Concept               | Description                                                                                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Hash Function**     | A function that maps keys to indices (buckets). Poor quality (e.g., weak randomness) can lead to clustering. Example: MurmurHash3 vs. simple modulo operations. |
| **Bucket/Slot Size**  | Number of entries per bucket. Larger sizes reduce collisions but increase memory per lookup.                                                       |
| **Load Factor**       | Ratio of elements to slots (e.g., 0.7–0.9 in Java’s `HashMap`). Affects rehashing frequency (costly operation).                                         |
| **Collision Resolution** | Mechanisms like chaining (linked lists) or open addressing (e.g., linear probing). Chaining scales poorly with collisions.                           |
| **Hash Partitioning** | Splitting keys into subsets (e.g., consistent hashing) to distribute load across nodes in distributed systems.                                              |
| **Adaptive Tuning**   | Dynamically adjusting parameters (e.g., resizing buckets) based on runtime metrics (e.g., collision rate).                                               |

---

### **Tuning Parameters**
| Parameter            | Tuning Options                                                                                     | Default Recommendations                                                                 |
|----------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Hash Function**    | - Custom (e.g., FNV-1a)<br>- Library (e.g., CityHash)<br>- Built-in (e.g., `std::hash`)            | Use industry-standard hashes (e.g., MurmurHash3) for uniformity.                         |
| **Bucket Size**      | Powers of 2 (e.g., 16, 64, 256) or dynamic (e.g., exponential growth)                           | Start with 16–128; grow when collision rate > 10%.                                      |
| **Load Factor (λ)**  | Static (e.g., 0.75) or adaptive (e.g., auto-resize at λ=0.95)                                  | 0.7–0.8 for balance between memory and ops.                                              |
| **Collision Handler**| - Chaining (linked lists)<br>- Open addressing (probing)<br>- Cuckoo hashing (non-colliding)      | Chaining for simplicity; open addressing for deterministic performance.                   |
| **Memory Overhead**  | Preallocate buckets or use sparse representations (e.g., Bloom filters for negatives)           | Preallocate if write-heavy; lazy allocate if read-heavy.                               |

---

### **Common Trade-offs**
| **Goal**               | **Tuning Lever**                          | **Trade-off**                                                                                   |
|------------------------|------------------------------------------|------------------------------------------------------------------------------------------------|
| Faster lookups         | Larger bucket size                       | Higher memory usage; more collisions if not resized properly.                                   |
| Lower memory usage     | Higher load factor (e.g., λ=0.9)         | Frequent rehashes (O(n) cost); increased collision probability.                                |
| Distributed scalability| Consistent hashing + partitioning      | Hotspots if not uniformly distributed (e.g., DNS-based requests).                              |
| Adaptive to spikes     | Dynamic resizing (e.g., exponential)    | Overhead from periodic rehashes; less predictable latency.                                   |

---

## **Schema Reference**
Below is a reference table for common hashing configurations. Adjust values based on workload (e.g., `write-heavy` vs. `read-heavy`).

| **Configuration**          | **Setting**                          | **Example**                          | **Use Case**                          |
|----------------------------|--------------------------------------|--------------------------------------|---------------------------------------|
| Hash Function              | Algorithm                            | MurmurHash3                          | General-purpose; uniform distribution |
| Bucket Initial Size        | Fixed (bytes/entries)                | 64KB (16 buckets × 4KB)              | Static workloads                      |
| Load Factor (λ)            | Threshold for resizing               | 0.8                                   | Balance memory/ops                     |
| Collision Resolution       | Method                               | Open addressing (quadratic probing)  | Cache systems                         |
| Resizing Strategy          | Growth factor                        | 2× or 1.5×                            | Mitigate thrashing                     |
| Memory Overhead            | Preallocation                        | 30% extra slots                      | Reduce fragmentation                  |
| Partitioning (Distributed) | Sharding key scheme                  | `(hash(key) % N) mod M`               | Horizontal scaling                     |

---

## **Query Examples**
### **1. Calculating Optimal Bucket Size**
**Scenario**: A cache with 1M entries, average key size of 16 bytes, and 50% load factor.
**Formula**:
Bucket size (bytes) = `(Total keys × Key size) / (Desired load factor × Target memory usage)`.
**Example**:
For 1M keys, 16B keys, λ=0.75, and 32GB target:
```
Total bytes = 1,000,000 × 16 = 16MB.
Buckets needed = 16MB / (0.75 × 32GB) ≈ 666 slots.
Bucket size = 32GB / 666 ≈ 48KB per bucket.
```

**SQL-like Pseudocode**:
```python
buckets_needed = (total_keys * key_size) / (load_factor * memory_limit)
bucket_size = memory_limit / buckets_needed
```

---

### **2. Dynamic Resizing Logic**
**Scenario**: Auto-resize when collision rate exceeds 5%.
**Implementation** (Pseudocode):
```python
if (collision_count / total_lookups) > 0.05:
    new_buckets = current_buckets * growth_factor  # 1.5× by default
    rehash_all_keys_into(new_buckets)
```

**Metrics to Monitor**:
- `collision_rate`: `(collisions / total_operations) × 100`
- `load_factor`: `current_keys / current_buckets`
- `rehash_time`: Latency spikes during resizing.

---

### **3. Distributed Hashing with Consistent Hashing**
**Scenario**: Distribute keys across 5 nodes.
**Algorithm**:
1. Assign each node a position in a 256-bit ring.
2. Hash keys and map to the next node clockwise.
**Example** (Python-like):
```python
def consistent_hash(key: str, nodes: List[str]) -> str:
    hash_val = hash(key)
    ring = sorted(hash(node) for node in nodes)
    for i in range(len(ring)):
        if ring[i] >= hash_val:
            return nodes[i]
    return nodes[0]  # Wrap around
```

**Query**:
```sql
-- Find node for key "user:123"
SELECT consistent_hash('user:123', ['node1', 'node2', 'node3'])
```

---

### **4. Mitigating Hash Clustering**
**Scenario**: Keys with similar prefixes (e.g., timestamps) collide frequently.
**Solutions**:
- **Salting**: Prepend random bytes to keys (e.g., `hash(salt + key)`).
  ```python
  def salted_hash(key: str, salt: bytes) -> int:
      return hash(salt + key.encode())
  ```
- **Two-Stage Hashing**: Use a secondary hash for sub-buckets.
  ```python
  def two_stage_hash(key: str, num_buckets: int) -> int:
      return (hash(key) % num_buckets, hash(key + str(num_buckets)) % 10)
  ```

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Pair With**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **[Caching]**             | Reduce expensive operations via in-memory storage.                         | Use hashing for cache key distribution (e.g., LRU eviction).                          |
| **[Sharding]**            | Split data across nodes to scale horizontally.                             | Apply consistent hashing for key routing.                                           |
| **[Bloom Filters]**       | Probabilistic membership tests to avoid disk lookups.                      | Combine with hashing to reduce false positives in large datasets.                    |
| **[Adaptive Concurrency]**| Dynamically adjust thread pools based on load.                           | Tune hash table concurrency (e.g., thread-local buckets) to reduce contention.      |
| **[Data Partitioning]**   | Split data into aligned chunks for parallel processing.                   | Use hashing to partition keys before processing (e.g., Hadoop’s `HashPartitioner`).  |

---

## **Troubleshooting**
| **Symptom**               | **Root Cause**                          | **Solution**                                                                          |
|---------------------------|----------------------------------------|--------------------------------------------------------------------------------------|
| High collision rate       | Poor hash function or uneven distribution | Switch to a better hash (e.g., xxHash) or repartition keys.                        |
| Memory bloat               | Over-provisioned buckets                | Monitor `load_factor`; resize when > 0.9.                                           |
| Rehashing performance drop | Thundering herd during resizing         | Use incremental rehashing or pause writes temporarily.                                |
| Hotspots in distributed   | Skewed key distribution                 | Add salt or use virtual nodes in consistent hashing.                                 |
| Garbage collection pauses  | Fragmented memory from dynamic resizing  | Preallocate or use generational allocators.                                          |

---

## **Best Practices**
1. **Benchmark First**:
   Use tools like [Google’s `xxHash`](https://github.com/Cyan4973/xxHash) or [Apache’s `HashMurmur`](https://github.com/apache/arrow/tree/master/cpp/src/arrow/hash/murmur) to compare hash functions under your workload.

2. **Profile Under Real Load**:
   Monitor collision rates and latency percentiles (e.g., p99) with tools like:
   - **Prometheus** + **Grafana** (for distributed systems).
   - **JVM Flight Recorder** (for Java `HashMap`).

3. **Avoid Anti-Patterns**:
   - **Fixed-size buckets**: Can lead to either memory waste or collisions.
   - **Bad salts**: E.g., using `key + 1` instead of cryptographic-grade salts.
   - **Ignoring rehashing cost**: Assume O(n) operations are free; test under load.

4. **Distributed Considerations**:
   - Use **virtual nodes** in consistent hashing to avoid single-node bottlenecks.
   - Design for **node failure**: Ensure failover doesn’t require rehashing all keys.

5. **Language-Specific Optimizations**:
   - **Java**: Prefer `ConcurrentHashMap` for thread safety.
   - **Python**: Use `dict` with `reserve()` for large static datasets.
   - **C++**: Leverage `std::unordered_map` with custom hashers (e.g., `absl::Hash`).

---
**Example Tuning Workflow**:
1. **Profile**: Detect 30% collisions in a 1M-entry cache.
2. **Analyze**: Hash function is `std::hash` (poor uniformity).
3. **Tune**: Replace with `CityHash` and resize buckets to 256K.
4. **Validate**: Collisions drop to <1% under load.

---
**See Also**:
- [CLH Hashing](https://en.wikipedia.org/wiki/Concurrent_hash_table#CLH_hash_table) (for lock-free concurrent access).
- [Ketama Algorithm](https://github.com/ketama/ketama) (for consistent hashing with virtual nodes).