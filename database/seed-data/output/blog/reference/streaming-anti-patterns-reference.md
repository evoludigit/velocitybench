# **[Pattern] Streaming Anti-Patterns Reference Guide**

---

## **Overview**
Streaming Anti-Patterns are common pitfalls in real-time data processing that degrade performance, increase complexity, or lead to incorrect results. Recognizing these pitfalls helps engineers design efficient, resilient, and maintainable streaming applications. This guide outlines key anti-patterns, their consequences, and best practices for mitigation.

Streaming systems must handle **event-time processing, stateful operations, backpressure, and fault tolerance**. Poorly implemented solutions often introduce **latency spikes, data skew, infinite loops, or resource starvation**, breaking core streaming guarantees. This guide categorizes anti-patterns into **architectural, operational, and algorithmic** issues and provides actionable fixes.

---

## **Anti-Patterns Schema Reference**

| **Category**          | **Anti-Pattern**               | **Description**                                                                                     | **Consequence**                                                                                     | **Mitigation**                                                                                     |
|-----------------------|--------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Architectural**     | **Event-Time vs. Processing-Time Misuse** | Using **processing time** (wall-clock) instead of **event time** for stateful operations.          | Incorrectly ordered results, skewed state updates, or missed events.                                | Use **watermarks** and **event timestamps** (e.g., Flink’s `EventTime` vs. `ProcessingTime`).     |
|                       | **Unbounded State Without Checks** | Storing state indefinitely without **TTL (time-to-live)** or **size limits**.                   | Unbounded memory growth, OOM crashes, or degraded performance.                                        | Apply **state TTLs** (e.g., Flink’s `StateTTL`) or **max state size** thresholds.                |
|                       | **Tightly Coupled Sources & Sinks** | Directly linking producers/consumers without buffering or **asynchronous decoupling**.            | **Cascading failures** (e.g., sink failure halts sources) or **throttling**.                        | Use **topic-based buffering** (Kafka) or **exactly-once sinks** (e.g., Flink’s `TwoPhaseCommit`).  |
| **Operational**       | **No Backpressure Handling**    | Ignoring **backpressure** (e.g., slow sinks or resource constraints).                                | **Data loss**, skew, or **resource exhaustion** (CPU/memory).                                      | Implement **dynamic scaling** (e.g., Kafka partitions) or **rate limiting** (e.g., Flink’s `backPressureEnabled`). |
|                       | **Flat-Map Over Usage**        | Using `flatMap` for **side effects** (e.g., logging, DB writes) instead of **data transformation**. | **Performance bottlenecks**, unpredictable throughput.                                              | Offload side effects to **asynchronous tasks** (e.g., `Async I/O` in Flink) or **sink operators**. |
|                       | **Stateful Operations Without Checkpoints** | Running long-running stateful logic **without checkpointing**.                      | **Permanent state loss** on failures (no recovery).                                                 | Enable **checkpointing** (e.g., Flink’s `checkpointInterval`) or **savepoints**.                 |
| **Algorithmic**       | **Windowing Without Watermarks** | Using **fixed windows** without **out-of-order event handling** (watermarks).                | **Duplicate windows**, missed data, or incorrect aggregations.                                      | Use **sliding/tumbling windows with watermarks** (e.g., `EventTimeSessionWindows`).                 |
|                       | **Join Key Skew**              | **Uneven key distribution** in joins (e.g., one key dominates traffic).                           | **Hot partitions**, slow queries, or **resource starvation**.                                        | **Salting keys** (add random prefixes) or **broadcast joins** for small datasets.                |
|                       | **Infinite Recursion in UDFs**  | Writing **recursive state updates** (e.g., `value = value + 1` in a loop).                      | **State explosion** or **deadlocks**.                                                              | Restructure logic to **non-recursive** or use **monotonic state updates**.                        |
| **Monitoring**        | **No observability for State**  | Lacking **metrics for state size, lag, or skew**.                                                  | Undetected **performance degradation** or **failures**.                                             | Track **state metrics** (e.g., Flink’s `MetricsRepository`) and **window lag**.                     |

---

## **Query Examples & Anti-Pattern Fixes**

### **1. Event-Time vs. Processing-Time**
**Anti-Pattern:**
```java
// Bad: Uses processing time for ordering (incorrect for delayed events)
dataStream.keyBy(...)
         .window(TumblingEventTimeWindows.of(Time.minutes(5)))
         .aggregate(new MyAggregateFunction())
         .addSink(...);
```
**Fix:**
```java
// Good: Uses event time with watermarks
dataStream.keyBy(...)
         .assignTimestampsAndWatermarks(
             WatermarkStrategy
                 .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                 .withTimestampAssigner(...)
         )
         .window(TumblingEventTimeWindows.of(Time.minutes(5)))
         .aggregate(...);
```

### **2. Unbounded State**
**Anti-Pattern:**
```java
// Bad: No TTL on state
ValueStateDescriptor<String> stateDesc =
    new ValueStateDescriptor<>("myState", String.class);
ValueState<String> state = getRuntimeContext().getState(stateDesc);
```
**Fix:**
```java
// Good: State with TTL (auto-clears after 10 mins)
stateDesc.enableTimeToLive(Time.minutes(10));
```

### **3. Join Key Skew**
**Anti-Pattern:**
```java
// Bad: Uneven key distribution (e.g., "user_123" dominates)
dataStreamA.join(dataStreamB)
          .where(...)
          .equalTo(...);
```
**Fix (Salting):**
```java
// Good: Distribute keys with a random prefix
Function<String, Tuple2<String, Integer>> saltingFn =
    key -> Tuple2.of(key + "_" + (int)(Math.random() * 10), key);
dataStreamA.keyBy(saltingFn).join(dataStreamB.keyBy(saltingFn))
          .where(...)
          .equalTo(...);
```

### **4. No Backpressure Handling**
**Anti-Pattern:**
```java
// Bad: No backpressure config (may crash on slow sinks)
env.setParallelism(1);
dataStream.addSink(new SlowSink());
```
**Fix:**
```java
// Good: Enable backpressure and dynamic scaling
env.setParallelism(8);
env.getConfig().enableForceThroughput();
dataStream.addSink(new SlowSink());
```

### **5. Stateful Operations Without Checkpoints**
**Anti-Pattern:**
```java
// Bad: No checkpointing (risk of state loss)
env.enableCheckpointing(5000); // Disabled!
```
**Fix:**
```java
// Good: Enable checkpointing + incremental checks
env.enableCheckpointing(5000, CheckpointingMode.EXACTLY_ONCE);
env.getCheckpointConfig().setCheckpointStorage("file:///checkpoints");
```

---

## **Related Patterns**
To counter anti-patterns, leverage these **complementary patterns**:

| **Pattern**                     | **Description**                                                                                 | **Use Case**                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Event Time Processing**         | Use **watermarks** and **event timestamps** for correct ordering.                               | Handling late-arriving data in aggregations.                                                   |
| **State Management**             | Apply **TTL** and **size limits** to state stores.                                            | Preventing unbounded memory growth in stateful apps.                                            |
| **Exactly-Once Processing**      | Use **checkpointing + idempotent sinks** for fault tolerance.                                   | Ensuring no data duplication or loss after failures.                                             |
| **Dynamic Scaling**              | Adjust **parallelism** based on **backpressure** or **load**.                                  | Handling spikes in throughput without OOM.                                                      |
| **Broadcast Joins**              | Optimize **skewed joins** with broadcast for small datasets.                                   | Efficiently joining hot keys with cold key sets.                                                 |
| **Async I/O**                    | Offload **side effects** (e.g., DB writes) asynchronously.                                      | Avoiding blocking operations in main stream.                                                    |
| **Micro-Batching**               | Process small batches instead of **one-by-one** in stateful ops.                              | Reducing overhead in windowed aggregations.                                                     |

---

## **Best Practices Summary**
1. **Always use event time** for stateful operations (avoid processing-time anti-patterns).
2. **Bound state** with TTLs or size limits to prevent memory leaks.
3. **Decouple producers/consumers** with buffering (e.g., Kafka topics).
4. **Monitor skew** in joins/aggregations and use salting or broadcast joins.
5. **Enable checkpointing** for stateful logic and **backpressure** for dynamic loads.
6. **Avoid side effects** in `flatMap`—offload to async tasks.
7. **Test anti-patterns** with **stress tests** (e.g., late data, backpressure).

---
**Further Reading:**
- [Flink Watermarks Docs](https://nightlies.apache.org/flink/flink-docs-stable/docs/stream/state/state_ttl/)
- [Kafka Backpressure Guide](https://kafka.apache.org/documentation/#backpressure)
- [Streaming Anti-Patterns (O’Reilly)](https://www.oreilly.com/library/view/streaming-data-with/9781492043633/)